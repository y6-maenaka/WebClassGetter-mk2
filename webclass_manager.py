import requests
import re
import time
import sys
import json

from bs4 import BeautifulSoup, Tag

# WebClassホームURL
webclass_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/"
# 講義ページホストURL
course_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/course.php/"
content_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/do_contents.php?reset_status=1"
m3u8_playlists_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/data/course/"

acs_pattern = r'acs_=(\w+)'
course_id_pattern = r'/course\.php/(.*?)/login\?'
content_id_pattern = r'set_contents_id=(.*)'
content_frame_url_pattern = r'window\.top\.location\.href="(.*?)"'
m3u8_video_redundant_url_pattern = r'txtbk_show_text\.php.*\.m3u8'
m3u8_parameter_pattern = re.compile(r'file=([^&%]+)%2F([^&]+\.m3u8)')



class WebClassContentControlBlock:
    def __init__(self ,video_name = None, content_page_url = None ,content_id = None, course = None ):
        self.video_name = video_name
        self.content_page_url = content_page_url
        self.content_id = content_id
        self.course = course
        self.content_m3u8_url = None

    def print__(self):
        print("video_name : ", self.video_name )
        print("content_page_url : ", self.content_page_url )
        print("content_id : ", self.content_id )
        print("course_id : ", self.course.id )
        print("content_m3u8_url : ", self.content_m3u8_url )




class WebClassCourse: # 講義コース管理用クラス
    def __init__(self, from_tag ):

        if not isinstance( from_tag , Tag ):
            return False

        self.name = from_tag.text # 講義名(全角)
        self.redirect_to = from_tag.get('href') # 講義ページリダイレクトURL
        self.id = None # 講義ID

        re_ret = re.search( course_id_pattern , self.redirect_to ) # 講義IDの取り出し
        if re_ret: self.id = re_ret.group(1)
        else: return False






def course_url( course_id , acs = None ): # 講義ページURL生成
    ret = course_base_url + str(course_id) + "/"
    if acs:
        ret += "?acs_=" + str(acs)
    return ret

def course_reset_url( course_id ): # コースを抜ける時は一旦resetしないと,別コースアクセスエラーが発生する
    ret = course_base_url + str(course_id) +"/logout"
    return ret

def content_page_url( content_id ):
    return content_base_url + "&" + "set_contents_id=" + str(content_id)

def m3u8_playlists_url( webclass_content_control_block , m3u8_url ):
    match = m3u8_parameter_pattern.search( m3u8_url )
    if not match:
        return None

    content_id = match.group(1)
    playlist_name = match.group(2)

    return m3u8_playlists_base_url + (webclass_content_control_block.course.id[:2]).lower() + "/" + webclass_content_control_block.course.id + "/" + content_id + "/" + playlist_name






class WebClassManager:
    def __init__(self, session ):

        self.session = session
        self.content_course_mapping = {} # コンテンツID : コースオブジェクト   ※ 多対一の構造
        self.prev_acs = None

        self.courses = [] # 全てのコース情報

        self.load_timetable() 


    def get_courses(self, log = True ): # ユーザが登録してるcourse_idを全て取得する
        #course_ids = []
        response = self.session.get( webclass_base_url )

        soup = BeautifulSoup( response.content , 'html.parser' )
        timetable = soup.find( id='schedule-table' ) # 時間割コンテナの取得
        timetable_columns = soup.find('tbody') # カラムの取得

        for column in timetable_columns:
            if not isinstance( column , Tag ):  # 不純物が混じる
                continue

            a_course_containers = column.find_all('a') # aタグのhrefに講義ID
            for i,a_tag in enumerate(a_course_containers):
                course = WebClassCourse( a_tag )
                if course: # 正常に取得できなければ追加しない
                    self.courses.append( course )

                if log:
                    print( "[#]" ,f'({i})' ,"  コース情報取得(済) :: " , course.name )

        return self.courses



    def get_content_ids(self, course, log = True ):

        ''' クエリパラメータacsを渡さないと強制ログアウトする 先ずダミーを送信してacsを取得 '''
        response = self.session.get( course_url(course_id=course.id) )
        re_ret = re.search( acs_pattern , response.text )
        if re_ret:
            acs = re_ret.group(1)

        content_ids = []

        response = self.session.get( course_url( course_id=course.id , acs = acs ) )
        soup = BeautifulSoup( response.content , 'html.parser' )

        content_h4_containers = soup.find_all('h4', class_='cm-contentsList_contentName')

        print("\nコース :: ", course.name )

        for i,content in enumerate(content_h4_containers):
            ret = content.find('a')
            if ret:
                mached_id = re.search( content_id_pattern , ret.get('href') )
                if mached_id:
                    content_id = mached_id.group(1) 
                    content_ids.append( content_id )
                    
                    if log:
                        print( "  +++ [##]" ,f'({i})' ,"  教材情報取得(済) -- " , content_id )

        response = self.session.get( course_reset_url(course_id=course.id) ) # これ実行しないと別コースアクセスエラーが発生する 例外の場合はキャッチする
        return content_ids



    def load_timetable(self):  # 時間割に登録されているコース内を全て探索して,course_idとcontent_idのマッピングを行う
        courses = self.get_courses()
        for course in courses:
            content_ids = self.get_content_ids( course )
            self.content_course_mapping.update({key:course for key in content_ids})


    def reverse_course_id_lookup(self, content_id ): # コンテンツID -> コースオブジェクトの逆引き 
        return self.content_course_mapping[content_id]

    def get_content_url(self, content_control_block ):
        '''
        1. コースページに飛ぶ
        2. コースページに飛ぶ
        2. chapterを読み込む
        3. scriptタグから取り出す
        ''' 

        response = self.session.get( course_url(content_control_block.course.id) ) # acs取得
        if response.status_code != 200:
            raise ConnectionError("acsの取得に失敗しました")
        re_ret = re.search( acs_pattern , response.text )
        if re_ret:
            acs = re_ret.group(1)


        response = self.session.get( course_url( content_control_block.course.id, acs=acs) )
        if response.status_code != 200:
            raise ConnectionError("コースページへのリダイレクトが失敗しました")
       
        # コンテンツページフレームHTMLの取得
        response = self.session.get( content_page_url(content_control_block.content_id) )
        if response.status_code != 200:
            raise ConnectionError("コンテンツページの取得に失敗しまいた")
   

        # コンテンツフレームのURLを抽出
        frame_url = re.search( content_frame_url_pattern , response.text ).group(1)
        if frame_url:
            frame_url.replace("/&amp;/g","&");
            frame_url = webclass_base_url + frame_url
        else:
            return None
   
        response = self.session.get( frame_url )
        if response.status_code != 200:
            raise ConnectionError("content frameの取得に失敗しました")

        soup = BeautifulSoup( response.content , 'html.parser' ) 
        chapter_src = soup.find('frame', {'name':'webclass_chapter'}) # コンテンツへのURLが埋め込まれているフレームURLの取得
        if not chapter_src:
            return None
        content_chapter_url = webclass_base_url + chapter_src.get('src')

        response = self.session.get( content_chapter_url ) # コンテンツへのURLが埋め込まれいるフレームの取得
        if response.status_code != 200:
            raise ConnectionError("chapter frameの取得に失敗しました")

        soup = BeautifulSoup( response.content , 'html.parser' )
        hls_container = soup.find('script', {'id': 'json-data'} ) # Hlsプレイヤースクリプトの取得
        if not hls_container:
            return None


        script_body = json.loads( hls_container.get_text() )
        m3u8_video_url_redundant = script_body.get('text_url') # m3u8動画のurlが含まれる文字列の取得
        if not m3u8_video_url_redundant:
            return None
       
        re_ret = re.search( m3u8_video_redundant_url_pattern , m3u8_video_url_redundant )
        if not re_ret:
            return None
        m3u8_video_url = re_ret.group(0)
    
        response = self.session.get( course_reset_url(content_control_block.course.id) ) # キャッチしてでも実行する(リフレッシュ)
        
        return m3u8_playlists_url( content_control_block , m3u8_video_url )
        




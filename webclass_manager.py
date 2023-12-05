import requests
import re
import time

from bs4 import BeautifulSoup, Tag


webclass_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/"
acs_pattern = r'acs_=(\w+)'
course_id_pattern = r'/course\.php/(.*?)/login\?'
content_id_pattern = r'set_contents_id=(.*)'


course_base_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/course.php/"


def course_url( course_id , acs = None ):
    ret = course_base_url + str(course_id) + "/"
    if acs:
        ret += "?acs_=" + str(acs)

    return ret

def course_reset_url( course_id ): # コースを抜ける時は一旦resetしないと,別コースアクセスエラーが発生する
    ret = course_base_url + str(course_id) +"/logout"
    return ret





class WebClassCourse:
    def __init__(self, anker_tag ):

        if not isinstance( anker_tag , Tag ):
            return False

        self.name = anker_tag.text
        self.redirect_to = anker_tag.get('href')
        self.id = None

        re_ret = re.search( course_id_pattern , self.redirect_to )
        if re_ret:
            self.id = re_ret.group(1)
        else:
            return False





class WebClassManager:
    def __init__(self, session ):

        self.session = session
        self.content_course_mapping = {}
        self.prev_acs = None

        # self.course_ids = [] # すべてのコース(講義)ID
        self.courses = [] # 全てのコース情報
        # self.content_ids = [] # 全てのコンテンツID

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


    def reverse_course_id_lookup(self, content_id ):
        return self.content_course_mapping[content_id]







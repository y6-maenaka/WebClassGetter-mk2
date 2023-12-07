import requests
import m3u8
import hashlib
import os
import threading

import ffmpeg # for join ts files to mp4
from webclass_manager import WebClassContentControlBlock

required_cookeis = {'WCAC':'Authenticated'}


class ConnectionError(Exception):
    pass
class ParameterNotFountError(Exception):
    pass






def assemble_video_from_ts_segments_list( downloader_id , ts_local_path_list , video_name , extension = ".mp4"):

    segments_file_path = "./ts_segments/" + "_" + str(downloader_id) + "segments_list" + ".txt"
    
    with open( segments_file_path ,"w") as file:
        lines = [f"file '{os.path.basename(line)}'" for line in ts_local_path_list] 
        file.write("\n".join(lines))
    
    return assemble_video_from_segments_lists_txt( downloader_id, segments_file_path, video_name, extension ) 



def assemble_video_from_segments_lists_txt( downloader_id, segments_list_path, video_name, extension = ".mp4" ):
    video_path = "./download_videos/"+ video_name + extension
    ffmpeg.input( segments_list_path , f="concat", safe=0).output( video_path ,c="copy").run() # tsファイルの読み込み






def m3u8_playlist_local_path( downloader_id ): # m3u8プレイリストのローカル保存用PATH生成
    return "./m3u8_playlists/" + "playlist_" + str(downloader_id) + ".m3u8"

def ts_segment_local_path( downloader_id , index ): # tsファイルのローカル保存用PATH生成
    return "./ts_segments/" + str(downloader_id) + "_" + "segment_" + str(index) + ".ts"

def ts_segment_url( ts_host , segment_id ): # tsファイルのダウンロード先URLの生成
    return ts_host + segment_id




def download_m3u8_video( downloader_id, m3u8_url, output_name, output_extension = ".mp4" ):
    splited_url = m3u8_url.split("/")
    parsed_url = splited_url[0:len(splited_url)-1]
    ts_host_url = "/".join(parsed_url) + "/"

    response = requests.get( m3u8_url , cookies = required_cookeis )
    if response.status_code != 200:
        return ConnectionError("m3u8プレイリストの取得に失敗ました")

    with open( m3u8_playlist_local_path( downloader_id ) , mode = 'wb' ) as file: #  プレイリストは一応保存しておく
        file.write(response.content)

    playlist = m3u8.load( m3u8_playlist_local_path(downloader_id) ) # m3u8ファイルのロード
        
    if not playlist: return False

    ts_total_count = len(playlist.segments)
    stored_segments = []

    for index, segment in enumerate(playlist.segments):
        #print( os.path.basename(segment.absolute_uri) ) # ファイル名だけ取得
        response = requests.get( ts_segment_url( ts_host_url , os.path.basename(segment.absolute_uri)) , cookies = required_cookeis )
        segment_local_path = ts_segment_local_path( downloader_id , index )
        print( "(" + str(downloader_id)+ ")" , "Downloading ..." , m3u8_url )

        with open( segment_local_path , mode = 'wb' ) as file:
            file.write(response.content)
        stored_segments.append( segment_local_path )
    
    assemble_video_from_ts_segments_list( downloader_id , stored_segments , output_name , output_extension )

    return True


   






'''
class m3u8Downloader: # 通常はマネージャーからメインスレッドと切り離して実行してもらう
    def __init__(self, downloader_id, m3u8_url , output_name, output_extension = ".mp4" ):
        self.id = 0
        self.m3u8_url = m3u8_url
        self.output_name = output_name
        self.output_extension = output_extension
        self.playlist = None

        splited_url = self.m3u8_url.split("/")
        parsed_url = splited_url[0:len(splited_url)-1]
        self.ts_host_url = "/".join(parsed_url) + "/"


    def get_m3u8_playlist(self): # 構成するtsファイルなどが書かれたファイルを収集する
        response = requests.get( self.m3u8_url , cookies = required_cookeis )
        if response.status_code != 200:
            return ConnectionError("m3u8プレイリストの取得に失敗ました")

        with open( m3u8_playlist_local_path( self.id ) , mode = 'wb' ) as file: #  プレイリストは一応保存しておく
            file.write(response.content)

        self.playlist = m3u8.load( m3u8_playlist_local_path(self.id) ) # m3u8ファイルのロード
        
        if not self.playlist: return False
        return True


    def start(self):
        if not self.get_m3u8_playlist(): # m3u8プレイリストの取得
            return False

        ts_total_count = len(self.playlist.segments)
        stored_segments = []

        for index, segment in enumerate(self.playlist.segments):
            #print( os.path.basename(segment.absolute_uri) ) # ファイル名だけ取得
            response = requests.get( ts_segment_url( self.ts_host_url , os.path.basename(segment.absolute_uri)) , cookies = required_cookeis )
            segment_local_path = ts_segment_local_path( self.id , index )
            print( segment_local_path )

            with open( segment_local_path , mode = 'wb' ) as file:
                file.write(response.content)
            stored_segments.append( segment_local_path )
        
        assemble_video_from_ts_segments_list( self.id , stored_segments , self.output_name , self.output_extension )

        return True
'''



class m3u8DownloaderManager:
    def __init__(self, requests_contents , thread_limit = 3 ):
        self.requests_contents = requests_contents
        self.thread_limit = thread_limit
    
    def start(self):

        pending_thread_queue = []
        for index, content in enumerate(self.requests_contents): # 無理矢理すぎ 修正する
            thread = threading.Thread( target = download_m3u8_video, args=( index, content.content_m3u8_url , content.video_name ) )
            pending_thread_queue.append(thread)
            thread.start()

        for _ in pending_thread_queue:
            _.join()
        



if __name__ == "__main__":
    downloader = m3u8Downloader( 1 , "https://webclass.eden.miyazaki-u.ac.jp/webclass/data/course/6c/6C530-2023/212312c07b7f584fdc288ef89d206c8e/playlist_1024x768&4x3.m3u8" , output_name= "テスト")
    flag = downloader.start()

    # assemble_ts_segments_with_segments_lists( 1 ,"./ts_segments/segments_list_0.txt" , "テスト" )
    

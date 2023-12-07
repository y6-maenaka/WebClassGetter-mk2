from sso_authenticator import SSOAuthenticator
from webclass_manager import WebClassManager, WebClassContentControlBlock
from m3u8_downloader_manager import m3u8DownloaderManager

from dotenv import load_dotenv
load_dotenv()
import os
import sys
import requests
import re


import yaml

requests_content_file_path = "./urls.yml"
content_id_pattern = r'set_contents_id=([^&]+)&language=([^&]+)'






if __name__ == "__main__":

    user_mid = os.getenv("MID") # MID
    if not user_mid:
        sys.exit("MIDが設定されていません")

    user_password = os.getenv("PASSWORD") # パスワード
    if not user_password:
        sys.exit("パスワードが設定されていません")



    session = requests.Session() # 共通セッションの作成(ダウンロードには必要ない)

    authenticator = SSOAuthenticator( session , user_mid , user_password )
    if not authenticator.complete_webclass_authenticate():
        sys.exit("SSO認証に失敗しました")

    webclass_manager = WebClassManager( session )

    
    m3u8_url_video_name_mapping = {}
    with open( requests_content_file_path, 'r') as yaml_file:
        requests_content_pairs = yaml.safe_load(yaml_file)

    webclass_content_control_blocks = []
    for video_name, raw_url in requests_content_pairs.items():
        re_ret = re.search( content_id_pattern , raw_url )
        if re_ret: content_id = re_ret.group(1)
        else: continue
        
        webclass_content_control_block = WebClassContentControlBlock(
                                                                     video_name=video_name,
                                                                     content_page_url=raw_url,
                                                                     content_id=content_id,
                                                                     course=webclass_manager.reverse_course_id_lookup(content_id) )
        m3u8_url = webclass_manager.get_content_url( webclass_content_control_block )
        if m3u8_url:
            webclass_content_control_block.content_m3u8_url = m3u8_url
            webclass_content_control_blocks.append( webclass_content_control_block )
        else: continue


    m3u8_downloader_manager = m3u8DownloaderManager( webclass_content_control_blocks )
    m3u8_downloader_manager.start()



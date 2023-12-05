from sso_authenticator import SSOAuthenticator
from webclass_manager import WebClassManager

from dotenv import load_dotenv
load_dotenv()
import os
import sys
import requests




if __name__ == "__main__":

    user_mid = os.getenv("MID") # MID
    if not user_mid:
        sys.exit("MIDが設定されていません")

    user_password = os.getenv("PASSWORD") # パスワード
    if not user_password:
        sys.exit("パスワードが設定されていません")


    session = requests.Session()


    authenticator = SSOAuthenticator( session , user_mid , user_password )
    if not authenticator.complete_webclass_authenticate():
        sys.exit("SSO認証に失敗しました")

    webclass_manager = WebClassManager( session )


    
   



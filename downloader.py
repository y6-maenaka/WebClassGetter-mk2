from sso_authenticator import SSOAuthenticator

from dotenv import load_dotenv
load_dotenv()
import os
import sys
import requests



univ_name = "miyazaki"

webclass_base_url = "https://webclass.eden." + univ_name + "-u.ac.jp/webclass/"
sso_authentication_base_url = "https://midp.cc." + univ_name + "-u.ac.jp/AccessManager/profile/SAML2/Redirect/SSO"
inquire_shibsession_cookie_url = "https://webclass.eden." + univ_name + "-u.ac.jp/Shibboleth.sso/SAML2/POST"





if __name__ == "__main__":

    user_mid = os.getenv("MID") # MID
    if not user_mid:
        sys.exit("MIDが設定されていません")

    user_password = os.getenv("PASSWORD") # パスワード
    if not user_password:
        sys.exit("パスワードが設定されていません")


    session = requests.Session()


    authenticator = SSOAuthenticator( session , user_mid , user_password )
    authenticator.complete_webclass_authenticate()


    print("Result")
    cookies_text = requests.utils.dict_from_cookiejar( session.cookies )
    for cookie in cookies_text:
        print(cookie)





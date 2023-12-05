from XML_SAMLResponse_parser import parse_from_xml_saml_response

import requests
import re



redirect_login_page_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/singlesignon.php?auth_mode=SHIB&auth_only=1"
sso_authentication_base_url = "https://midp.cc.miyazaki-u.ac.jp/AccessManager/profile/SAML2/Redirect/SSO"
webclass_sp_authentication_url = "https://webclass.eden.miyazaki-u.ac.jp/Shibboleth.sso/SAML2/POST"






class SSOAuthenticator:

    def __init__(self, session ,mid , password):
        self.session = session
        self.mid = mid
        self.password = password

        self.execution_pattern = r'execution=([^&]+)'


    def sso_authenticate(self): # SSOサーバへの認証プロセスを完了する
        response = self.session.get( redirect_login_page_url ) #login時に必要なクエリパタメータ(jsessionid, execution)の取得
        if( response.status_code != 200 ): 
            return False

        cookies_text = requests.utils.dict_from_cookiejar( self.session.cookies )
        jsessionid = cookies_text["JSESSIONID"] # set-cookieされたものを取得する
        if not jsessionid:
            return False

        ret = re.search( self.execution_pattern, response.url ) # urlに含まれるexecutionの取得
        if ret: 
            execution = ret.group(1) # executionの取得
        else:
            return False

        sso_authentication_url = sso_authentication_base_url
        sso_authentication_url += ";jsessionid=" + str(jsessionid)
        sso_authentication_url += "?execution=" + str(execution)

        payload = {
                  'j_username': str(self.mid),
                  'j_password' : str(self.password),
                  '_eventId_proceed': 'ログイン' # 固定
                }

        response = self.session.post( sso_authentication_url , data = payload ) # SAMLを取得する
        if( response.status_code != 200 ): 
            return False
        
        self.acs_url, self.relay_state, self.saml_response = parse_from_xml_saml_response( response.text ) # relay_stateとsamle_responseはいずれもエンコードされたまま そのままで大丈夫

        return True


    def sp_webclass_authenticate(self, relay_state , saml_response ): # SPにSAML情報を送信して,トークン(cookie)を取得する
        
       payload = {
                "RelayState" : str(relay_state),
                "SAMLResponse" : str(saml_response)
        }

       response = self.session.post( webclass_sp_authentication_url , data = payload ) # webclass_sp_authentication_urlにgetすることで,token(cookie)を得る

       # 目的のspでの認証用token(cookie)が正常に取得されているかチェック(数も少ない為全探索方式で)
       cookies_text = requests.utils.dict_from_cookiejar( self.session.cookies )
       mached_shibsession = [ cookie for cookie in cookies_text if cookie.startswith('_shibsession') ]
       if not mached_shibsession: # 正常にcookieが取得されていない場合
           return False

       return True


    def complete_webclass_authenticate(self):

        if not self.sso_authenticate():
            return False

        if not self.sp_webclass_authenticate( self.relay_state , self.saml_response ):
            return False

        # webclass(SP)への認証が正常に完了
        return True





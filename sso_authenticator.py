from XML_saml_response_parser import parse_from_xml_saml_response

import requests
import re
import sys



# このリンクにアクセスすると,認証ようクエリパラメータが勝手にセットされるので,ログイン時はこのリンクを踏むと良い
redirect_login_page_url = "https://webclass.eden.miyazaki-u.ac.jp/webclass/singlesignon.php?auth_mode=SHIB&auth_only=1" 
# ログイン情報送先
sso_authentication_base_url = "https://midp.cc.miyazaki-u.ac.jp/AccessManager/profile/SAML2/Redirect/SSO"
# SP認証用tokenの取得先(sso認証情報を渡す)
webclass_sp_authentication_url = "https://webclass.eden.miyazaki-u.ac.jp/Shibboleth.sso/SAML2/POST"

# ログインん用クエリパラメータのパターン
execution_pattern = r'execution=([^&]+)' 



class SSOConnectionError(Exception):
    pass
class ParameterNotFountError(Exception):
    pass




class SSOAuthenticator:

    def __init__(self, session ,mid , password):
        self.session = session # 共通セッション
        self.mid = mid  # ログイン情報(id)
        self.password = password # ログイン情報(pass)


    def sso_authenticate(self): # SSOサーバへの認証プロセスを完了する
        response = self.session.get( redirect_login_page_url ) #login時に必要なクエリパタメータ(jsessionid, execution)の取得
        if( response.status_code != 200 ): 
            raise SSOConnectionError("SSO認証サーバとの通信に失敗しました")

        cookies_text = requests.utils.dict_from_cookiejar( self.session.cookies ) # SSOサーバへのPOSTにこのcookieがクエリパラメータとしてが必要
        jsessionid = cookies_text["JSESSIONID"] # set-cookieされたものを取得する
        if not jsessionid:
            raise ParameterNotFountError("jsessionidの取得に失敗しました")

        re_ret = re.search( execution_pattern, response.url )  # SSOサーバへのPOSTにこのcookieがクエリパラメータとしてが必要
        if re_ret: execution = re_ret.group(1) # executionの取得
        else: raise ParameterNotFountError("executionの取得に失敗しました")

        sso_authentication_url = sso_authentication_base_url # ログイン情報POST先urlの生成
        sso_authentication_url += ";jsessionid=" + str(jsessionid)
        sso_authentication_url += "?execution=" + str(execution)

        payload = {
                  'j_username': str(self.mid),
                  'j_password' : str(self.password),
                  '_eventId_proceed': 'ログイン' # 固定
                }

        response = self.session.post( sso_authentication_url , data = payload ) # SAMLを取得する
        if( response.status_code != 200 ): 
            raise SSOConnectionError("SSOサーバとの通信に失敗しました")
        
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
           return ParameterNotFountError("_shibsession(SP:token)の取得に失敗しました")

       return True


    def complete_webclass_authenticate(self): # SSO認証とSP認証を完了させる

        if not self.sso_authenticate():
            sys.exit("SSO認証に失敗しました")

        if not self.sp_webclass_authenticate( self.relay_state , self.saml_response ):
            sys.exit("WebClass認証に失敗しました")

        # webclass(SP)への認証が正常に完了
        return True





from xml.etree import ElementTree as ET



def parse_from_xml_saml_response( from_string ):
    
    root = ET.fromstring( str(from_string) )
    if not root: return False

    assertion_form = root.find(".//form") # SAMLResponseはformに含まれる
    if not assertion_form: return False

    acs_url = assertion_form.get("action") # 転送先(SP)のurl
    if not acs_url: return False
    relay_state = assertion_form.find(".//input[@name='RelayState']").get('value') # RelayState
    if not relay_state: return False
    saml_response = assertion_form.find(".//input[@name='SAMLResponse']").get('value') # SAMLResponse デコードしない そのまま使用する
    if not saml_response: return False

    return acs_url, relay_state, saml_response

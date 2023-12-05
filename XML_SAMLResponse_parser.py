from xml.etree import ElementTree as ET



def parse_from_xml_saml_response( from_string ):
    
    root = ET.fromstring( str(from_string) )
    assertion_form = root.find(".//form") # SAMLResponseはformに含まれる

    acs_url = assertion_form.get("action") # 転送先(SP)のurl
    relay_state = assertion_form.find(".//input[@name='RelayState']").get('value') # RelayState
    saml_response = assertion_form.find(".//input[@name='SAMLResponse']").get('value') # SAMLResponse デコードしない そのまま使用する

    return acs_url, relay_state, saml_response

from .namespaces import ENS, MNS, SNS, TNS, NSMAP

class MissingResponseCode(Exception): pass
class UnknownError(Exception): pass

ERRORS = {
    "ErrorNameResolutionNoResults": None,
    "NoError": None
}

def GetError(response_xml):
    # find the response code
    response_code = response_xml.find(".//{%s}ResponseCode" % MNS)
    if response_code is None:
        response_code = response_xml.find(".//{%s}ResponseCode" % ENS)

    # check for error
    if response_code is None:
        return MissingResponseCode("Response code not found.")
    if response_code.text not in ERRORS:
        return UnknownError(response_code.text)
    return ERRORS[response_code.text]

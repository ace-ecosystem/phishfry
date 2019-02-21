from .namespaces import ENS, MNS, SNS, TNS, NSMAP

class MailboxNotFound(Exception): pass
class MessageNotFound(Exception): pass
class MissingResponseCode(Exception): pass
class UnknownError(Exception): pass

ERRORS = {
    "ErrorNameResolutionNoResults": MailboxNotFound("Mailbox not found"),
    "ErrorNonExistentMailbox": MailboxNotFound("Mailbox not found"),
    "NoError": None
}

def GetError(response_xml):
    # find the response code
    response_codes = response_xml.findall(".//{%s}ResponseCode" % MNS)
    if len(response_codes) == 0:
        response_code = response_xml.findall(".//{%s}ResponseCode" % ENS)

    # check for error
    if len(response_codes) == 0:
        return MissingResponseCode("Response code not found.")
    for response_code in response_codes:
        if response_code.text not in ERRORS:
            return UnknownError(response_code.text)
        return ERRORS[response_code.text]

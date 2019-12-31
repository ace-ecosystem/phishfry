from io import BytesIO
import logging

from lxml import etree
import requests
import requests_ntlm

from .errors import GetError, MailboxNotFound
from .mailbox import Mailbox
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from .remediation_result import RemediationResult


log = logging.getLogger(__name__)


BASIC = "basic"
NTLM = "ntlm"


AUTH_TYPES_MAP = {
    BASIC: requests.auth.HTTPBasicAuth,
    NTLM: requests_ntlm.HttpNtlmAuth,
}


def get_auth(auth_type, user, password):
    """Return requests.Session.auth-compatible authentication object."""

    logging.debug("getting auth type")

    if auth_type == NTLM:
        # XXX - Should we look for backslashes first?
        user = f"\\{user}"

    try:
        auth_object = AUTH_TYPES_MAP[auth_type](user, password)
    except KeyError:
        message = f"auth type {auth_type} not supported by phishfry"
        logging.error(message)
        raise ValueError(message)
    else:
        logging.debug(f"created {auth_object.__class__.__name__} for auth type {auth_type}")
        return auth_object


class Account():
    def __init__(
        self,
        user,
        password,
        server="outlook.office365.com",
        version="Exchange2016",
        timezone="UTC",
        proxies={},
        adapter=requests.adapters.HTTPAdapter(),
        auth_type=BASIC,
    ):
        self.version = version
        self.session = requests.Session()
        self.user = user
        self.session.auth = get_auth(auth_type, user, password)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({'Content-Type': 'text/xml; charset=utf-8', 'Accept-Encoding': 'gzip, deflate'})
        self.url = "https://{}/EWS/Exchange.asmx".format(server)
        self.timezone = timezone
        self.session.proxies = proxies

    def SendRequest(self, request, impersonate=None):
        headers = {}

        # create a soap envelope
        soap = etree.Element("{%s}Envelope" % SNS, nsmap=NSMAP)

        # create envelope headers section
        soap_header = etree.SubElement(soap, "{%s}Header" % SNS)

        # add requested server version header
        request_server_version = etree.SubElement(soap_header, "{%s}RequestServerVersion" % TNS, Version=self.version)

        # add impersonate header if impersonating a user
        if impersonate is not None:
            exchange_impersonation = etree.SubElement(soap_header, "{%s}ExchangeImpersonation" % TNS)
            connecting_sid = etree.SubElement(exchange_impersonation, "{%s}ConnectingSID" % TNS)
            primary_smtp_address = etree.SubElement(connecting_sid, "{%s}PrimarySmtpAddress" % TNS)
            primary_smtp_address.text = impersonate
            headers["X-AnchorMailbox"] = impersonate

        # add timezone context header
        timezone_context = etree.SubElement(soap_header, "{%s}TimeZoneContext" % TNS)
        timezone_definition = etree.SubElement(timezone_context, "{%s}TimeZoneDefinition" % TNS, Id=self.timezone)

        # create body
        soap_body = etree.SubElement(soap, "{%s}Body" % SNS)

        # add request to soap envelope body
        soap_body.append(request)

        # serialize request
        request_xml = etree.tostring(soap, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")

        # send request
        log.debug(request_xml)
        response = self.session.post(self.url, data=request_xml, headers=headers)

        # parse response
        response_xml = etree.parse(BytesIO(response.text.encode("utf-8")))
        log.debug(etree.tostring(response_xml, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8"))

        # raise any errors
        error = GetError(response_xml)
        if error is not None:
            raise error

        # return the reponse xml
        return response_xml

    # returns the mailbox for the address
    def GetMailbox(self, address):
        # create resolve name request
        resolve_names = etree.Element("{%s}ResolveNames" % MNS, ReturnFullContactData="false")
        unresolved_entry = etree.SubElement(resolve_names, "{%s}UnresolvedEntry" % MNS)
        unresolved_entry.text = "smtp:{}".format(address)

        # send the request
        try:
            response = self.SendRequest(resolve_names)
        except MailboxNotFound as e:
            return None

        # return mailbox object from xml
        return Mailbox(self, response.find(".//{%s}Mailbox" % TNS))

    # remediate a message for an address
    def Remediate(self, action, address, message_id, spider):
        mailbox = self.GetMailbox(address)
        if mailbox is None:
            return { address: RemediationResult(address, message_id, "Unknown", action, success=False, message="Mailbox not found") }
        return mailbox.Remediate(action, message_id, spider)

    # delete a message for an address
    def Remove(self, address, message_id, spider=False):
        return self.Remediate("remove", address, message_id, spider)

    # restore a message for an address
    def Restore(self, address, message_id, spider=False):
        return self.Remediate("restore", address, message_id, spider)

    # get inbox rules for an address
    def GetInboxRules(self, address):
        mailbox = self.GetMailbox(address)
        if mailbox is None:
            return False
        mailbox.GetInboxRules()
        return True

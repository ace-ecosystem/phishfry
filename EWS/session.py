from .errors import GetError
from io import BytesIO
import logging
from lxml import etree
from .mailbox import Mailbox
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
import requests

log = logging.getLogger(__name__)

class Session():
    def __init__(self, user, password, server="outlook.office365.com", version="Exchange2016", timezone="UTC"):
        self.version = version
        self.session = requests.Session()
        self.user = user
        self.session.auth = (user, password)
        self.session.headers.update({'Content-Type': 'text/xml; charset=utf-8', 'Accept-Encoding': 'gzip, deflate'})
        self.url = "https://{}/EWS/Exchange.asmx".format(server)
        self.timezone = timezone

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

    def ExpandMailbox(self, mailbox, expanded_addresses=None):
        if mailbox.mailbox_type == "PublicDL" or mailbox.mailbox_type == "GroupMailbox":
            # do not expand the same address twice
            if expanded_addresses is None:
                expanded_addresses = {}
            if mailbox.address in expanded_addresses:
                return {}
            expanded_addresses[mailbox.address] = True

            # create expand dl request
            expand_dl = etree.Element("{%s}ExpandDL" % MNS)
            m_elem = etree.SubElement(expand_dl, "{%s}Mailbox" % MNS)
            address = etree.SubElement(m_elem, "{%s}EmailAddress" % TNS)
            address.text = mailbox.address

            # send the request
            response = self.SendRequest(expand_dl)
            
            # recursively expand distribution lists
            if mailbox.mailbox_type == "PublicDL":
                members = {}
                for mailbox_elem in response.findall(".//{%s}Mailbox" % TNS):
                    member = Mailbox(self, mailbox_elem)
                    members.update(self.ExpandMailbox(member, expanded_addresses=expanded_addresses))
                return members

            # only return the first mailbox for groups to prevent extra calls to server
            else:
                for mailbox_elem in response.findall(".//{%s}Mailbox" % TNS):
                    member = Mailbox(self, mailbox_elem, group=mailbox.xml)
                    if member.mailbox_type == "Mailbox":
                        return { member.address: member }
                return {}

        elif mailbox.mailbox_type == "Mailbox":
            return { mailbox.address: mailbox }

    # returns all mailboxes the address delivers to
    def Resolve(self, address):
        # create resolve name request
        resolve_names = etree.Element("{%s}ResolveNames" % MNS, ReturnFullContactData="false")
        unresolved_entry = etree.SubElement(resolve_names, "{%s}UnresolvedEntry" % MNS)
        unresolved_entry.text = "smtp:{}".format(address)

        # send the request
        response = self.SendRequest(resolve_names)

        # create mailbox object from xml
        mailbox = Mailbox(self, response.find(".//{%s}Mailbox" % TNS))

        # expand groups and distribution lists
        return list(self.ExpandMailbox(mailbox).values())

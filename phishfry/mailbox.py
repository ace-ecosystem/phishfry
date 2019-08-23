from .errors import MailboxNotFound, MessageNotFound
from .folder import Folder, DistinguishedFolder
import logging
from lxml import etree
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from .remediation_result import RemediationResult
from .restriction import Restriction, IsEqualTo

log = logging.getLogger(__name__)

class Mailbox():
    def __init__(self, account, xml, group=None):
        self.account = account
        self.group = group
        self.address = xml.find("{%s}EmailAddress" % TNS).text.lower()
        self.mailbox_type = xml.find("{%s}MailboxType" % TNS).text

    @property
    def display_address(self):
        if self.group is None:
            return self.address
        return self.group.address

    @property
    def AllItems(self):
        # create find folder request
        find_folder = etree.Element("{%s}FindFolder" % MNS, Traversal="Shallow")
        folder_shape = etree.SubElement(find_folder, "{%s}FolderShape" % MNS)
        base_shape = etree.SubElement(folder_shape, "{%s}BaseShape" % TNS)
        base_shape.text = "IdOnly"
        find_folder.append(Restriction(IsEqualTo("folder:DisplayName", "AllItems")))
        parent_folder = etree.SubElement(find_folder, "{%s}ParentFolderIds" % MNS)
        parent_folder.append(DistinguishedFolder(self, "root").ToXML())

        # send the request
        response = self.account.SendRequest(find_folder, impersonate=self.address)

        return Folder(self, response.find(".//{%s}FolderId" % TNS))

    @property
    def RecoverableItems(self):
        return DistinguishedFolder(self, "recoverableitemsdeletions")

    def ToXML(self, namespace=TNS):
        mailbox = etree.Element("{%s}Mailbox" % namespace)
        email_address = etree.SubElement(mailbox, "{%s}EmailAddress" % TNS)
        email_address.text = self.address
        return mailbox

    def Expand(self):
        # create expand dl request
        expand_dl = etree.Element("{%s}ExpandDL" % MNS)
        expand_dl.append(self.ToXML(namespace=MNS))

        # send the request
        response = self.account.SendRequest(expand_dl)
        
        # get list of members from response
        members =[Mailbox(self.account, m) for m in response.findall(".//{%s}Mailbox" % TNS)]
        log.info("members = {}".format([m.address for m in members]))
        return members

    def GetOwner(self):
        # create expand dl request
        expand_dl = etree.Element("{%s}ExpandDL" % MNS)
        expand_dl.append(self.ToXML(namespace=MNS))

        # send the request
        response = self.account.SendRequest(expand_dl)
        
        # return the first real mailbox
        for m in response.findall(".//{%s}Mailbox" % TNS):
            mailbox = Mailbox(self.account, m, group=self)
            if mailbox.mailbox_type == "Mailbox":
                return mailbox
        raise Exception("Owner not found")

    def GetInboxRules(self):
        # create get rules request
        get_rules = etree.Element("{%s}GetInboxRules" % MNS)
        mailbox_address = etree.SubElement(get_rules, "{%s}MailboxSmtpAddress" % MNS)
        mailbox_address.text = self.address

        # send the request
        response = self.account.SendRequest(get_rules)

    def FindRecipients(self, messages, message_id, seen_message_ids):
        # get list of all messages which are not the original message
        forwarded_messages = []
        for message in messages:
            if message.message_id not in seen_message_ids:
                forwarded_messages.append(message)
                seen_message_ids[message.message_id] = True

        # if there are no forwards/replies then return empty list
        if len(forwarded_messages) == 0:
            return []

        # create get item request
        get_item = etree.Element("{%s}GetItem" % MNS)
        item_shape = etree.SubElement(get_item, "{%s}ItemShape" % MNS)
        base_shape = etree.SubElement(item_shape, "{%s}BaseShape" % TNS)
        base_shape.text = "IdOnly"
        additional_properties = etree.SubElement(item_shape, "{%s}AdditionalProperties" % TNS)
        etree.SubElement(additional_properties, "{%s}FieldURI" % TNS, FieldURI="message:ToRecipients")
        etree.SubElement(additional_properties, "{%s}FieldURI" % TNS, FieldURI="message:CcRecipients")
        etree.SubElement(additional_properties, "{%s}FieldURI" % TNS, FieldURI="message:BccRecipients")
        item_ids = etree.SubElement(get_item, "{%s}ItemIds" % MNS)
        for message in forwarded_messages:
            item_ids.append(message.ToXML())

        # send the request
        response = self.account.SendRequest(get_item, impersonate=self.address)

        # get all recipients from response
        recipients = [Mailbox(self.account, m) for m in response.findall(".//{%s}Mailbox" % TNS)]

        if len(recipients) > 0:
            log.info("forwarded to {}".format([r.address for r in recipients]))

        return recipients

    def CreateRemediationRequest(self, action):
        # return delete request
        if action == "remove":
            return etree.Element("{%s}DeleteItem" % MNS, DeleteType="SoftDelete")

        # return restore request
        request = etree.Element("{%s}MoveItem" % MNS)
        to_folder = etree.SubElement(request, "{%s}ToFolderId" % MNS)
        to_folder.append(DistinguishedFolder(self, "inbox").ToXML())
        return request

    def Remediate(self, action, message_id, spider, results=None, seen_message_ids=None):
        # don't retrieve recipients for the same message twice
        if seen_message_ids is None:
            seen_message_ids = { message_id: True }

        # don't process the same address twice
        if results is None:
            results = {}
        if self.group is None:
            if self.display_address in results:
                return
            results[self.address] = RemediationResult(self.address, message_id, self.mailbox_type, action)
            log.info("{}ing {} {}".format(action[:-1], self.display_address, message_id))

        try:
            # remediate from the group owner's mailbox
            if self.mailbox_type == "GroupMailbox":
                owner = self.GetOwner()
                results[self.display_address].owner = owner.address
                owner.Remediate(action, message_id, spider, results=results, seen_message_ids=seen_message_ids)

            # remediate for all members of distribution list
            elif self.mailbox_type == "PublicDL":
                members = self.Expand()
                results[self.display_address].result("{}d".format(action), success=True)
                for member in members:
                    results[self.display_address].members.append(member.address)
                    member.Remediate(action, message_id, spider, results=results, seen_message_ids=seen_message_ids)

            # remediate message for mailbox
            elif self.mailbox_type == "Mailbox":
                # find all messages with message_id
                messages = []
                if action == "remove":
                    messages = self.AllItems.Find(message_id, spider)
                else:
                    messages = self.RecoverableItems.Find(message_id, spider)

                # get list of recipients the messsage was forwarded to
                forwards = []
                if spider:
                    forwards = self.FindRecipients(messages, message_id, seen_message_ids)

                # create remediation request
                request = self.CreateRemediationRequest(action)
                item_ids = etree.SubElement(request, "{%s}ItemIds" % MNS)
                for message in messages:
                    item_ids.append(message.ToXML())

                # send the request
                response = self.account.SendRequest(request, impersonate=self.address)

                # mark as successful
                results[self.display_address].result("{}d".format(action), success=True)

                # remediate for forwarded recipients
                for recipient in forwards:
                    results[self.display_address].forwards.append(recipient.address)
                    recipient.Remediate(action, message_id, spider, results=results, seen_message_ids=seen_message_ids)

            # mailbox is external
            else:
                raise MailboxNotFound("Mailbox not found")

        # set result if Message not found
        except MessageNotFound as e:
            # stil consider delete successful since the message is already deleted
            success = action == "remove"
            results[self.display_address].result(str(e), success=success)

        # set result error if exception is raised
        except Exception as e:
            results[self.display_address].result(str(e))

        # return results
        return results

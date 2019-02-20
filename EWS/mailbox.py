from .errors import MailboxNotFound
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
        self.address = xml.find("{%s}EmailAddress" % TNS).text
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
        log.info("expanding {}".format(self.address))

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
        log.info("getting owner of {}".format(self.address))

        # create expand dl request
        expand_dl = etree.Element("{%s}ExpandDL" % MNS)
        expand_dl.append(self.ToXML(namespace=MNS))

        # send the request
        response = self.account.SendRequest(expand_dl)
        
        # return the first real mailbox
        for m in response.findall(".//{%s}Mailbox" % TNS):
            mailbox = Mailbox(self.account, m, group=self)
            if mailbox.mailbox_type == "Mailbox":
                log.info("owner = {}".format(mailbox.address))
                return mailbox
        return None

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

    def Remediate(self, action, message_id, results=None, seen_message_ids=None):
        # don't retrieve recipients for same message twice
        if seen_message_ids is None:
            seen_message_ids = { message_id: True }

        # don't process the same address twice
        if results is None:
            results = {}
        if self.group is None:
            if self.display_address in results:
                return
            results[self.display_address] = RemediationResult(self.mailbox_type)

        # log action
        log.info("{} ({}, {})".format(action, self.display_address, message_id))

        # remediate from the group owner's mailbox
        if self.mailbox_type == "GroupMailbox":
            try:
                owner = self.GetOwner()
            except Exception as e:
                log.info(e)
                results[self.display_address].message = str(e)
                results[self.display_address].success = False
                return results

            results[self.display_address].owner = owner.address
            if owner is not None:
                owner.Remediate(action, message_id, results=results, seen_message_ids=seen_message_ids)

        # remediate for all members of distribution list
        elif self.mailbox_type == "PublicDL":
            try:
                members = self.Expand()
            except Exception as e:
                log.info(e)
                results[self.display_address].message = str(e)
                results[self.display_address].success = False
                return results

            results[self.display_address].members = [m.address for m in members]
            for member in members:
                member.Remediate(action, message_id, results=results, seen_message_ids=seen_message_ids)

        # remediate message in mailbox
        elif self.mailbox_type == "Mailbox":
            # find all messages with message_id
            messages = []
            try:
                if action == "delete":
                    messages = self.AllItems.Find(message_id)
                else:
                    messages = self.RecoverableItems.Find(message_id)
            except Exception as e:
                log.info(e)
                results[self.display_address].message = str(e)
                results[self.display_address].success = False
                return results

            # if messages were found
            if len(messages) > 0:
                # get list of recipients the messsage was forwarded to
                try:
                    forwards = self.FindRecipients(messages, message_id, seen_message_ids)
                except Exception as e:
                    log.info(e)
                    results[self.display_address].message = str(e)
                    results[self.display_address].success = False
                    return results

                # create delete request
                if action == "delete":
                    request = etree.Element("{%s}DeleteItem" % MNS, DeleteType="SoftDelete")

                # create restore request
                else:
                    request = etree.Element("{%s}MoveItem" % MNS)
                    to_folder = etree.SubElement(request, "{%s}ToFolderId" % MNS)
                    to_folder.append(DistinguishedFolder(self, "inbox").ToXML())

                # add item ids to request
                item_ids = etree.SubElement(request, "{%s}ItemIds" % MNS)
                for message in messages:
                    item_ids.append(message.ToXML())

                # send the request
                try:
                    response = self.account.SendRequest(request, impersonate=self.address)
                    log.info("{}d".format(action))
                    results[self.display_address].message = "{}d".format(action)
                except Exception as e:
                    log.info(e)
                    results[self.display_address].message = str(e)
                    results[self.display_address].success = False
                    return results

                # remediate for forwarded recipients
                if len(forwards) > 0:
                    results[self.display_address].forwards = [f.address for f in forwards]
                for recipient in forwards:
                    recipient.Remediate(action, message_id, results=results, seen_message_ids=seen_message_ids)

            # message not found
            else:
                results[self.display_address].message = "Message not found"
                if action == "restore":
                    results[self.display_address].success = False
                log.info("message not found")

        # mailbox is external
        else:
            results[self.display_address].message = "Mailbox not found"
            results[self.display_address].success = False
            log.info("mailbox not found")

        return results

    def Delete(self, message_id):
        return self.Remediate("delete", message_id)

    def Restore(self, message_id):
        return self.Remediate("restore", message_id)

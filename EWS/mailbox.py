from .errors import MailboxNotFound
from .folder import Folder, DistinguishedFolder
import logging
from lxml import etree
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
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
        log.info("Expanding {} distribution list".format(self.address))

        # create expand dl request
        expand_dl = etree.Element("{%s}ExpandDL" % MNS)
        expand_dl.append(self.ToXML(namespace=MNS))

        # send the request
        try:
            response = self.account.SendRequest(expand_dl)
        except MailboxNotFound:
            pass
        
        # get list of members from response
        members =[Mailbox(self.account, m) for m in response.findall(".//{%s}Mailbox" % TNS)]

        log.info("Members of {} = {}".format(self.address, [m.address for m in members]))

    def GetOwner(self):
        log.info("Getting owner of {} group".format(self.address))

        # create expand dl request
        expand_dl = etree.Element("{%s}ExpandDL" % MNS)
        expand_dl.append(self.ToXML(namespace=MNS))

        # send the request
        try:
            response = self.account.SendRequest(expand_dl)
        except MailboxNotFound:
            pass
        
        # return the first real mailbox
        for m in response.findall(".//{%s}Mailbox" % TNS):
            mailbox = Mailbox(self.account, m, group=self)
            if mailbox.mailbox_type == "Mailbox":
                log.info("Owner of {} group is {}".format(self.address, mailbox.address))
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
            log.info("{} sent {} to {}".format(self.display_address, message_id, [r.address for r in recipients]))

        return recipients

    def Delete(self, message_id, deleted=None, seen_message_ids=None):
        if seen_message_ids is None:
            seen_message_ids = { message_id: True }

        # don't delete from the same address twice
        if deleted is None:
            deleted = {}
        if self.group is None:
            if self.address in deleted:
                return
            deleted[self.address] = True

        # delete from the group owner's mailbox
        if self.mailbox_type == "GroupMailbox":
            owner = self.GetOwner()
            if owner is not None:
                owner.Delete(message_id, deleted=deleted, seen_message_ids=seen_message_ids)

        # delete from all members of distribution list
        elif self.mailbox_type == "PublicDL":
            members = self.Expand()
            for member in members:
                member.Delete(message_id, deleted=deleted, seen_message_ids=seen_message_ids)

        # delete message from mailbox
        else:
            # find all messages with message_id
            messages = self.AllItems.Find(message_id)

            # delete message from anyone the message was forwarded to
            for recipient in self.FindRecipients(messages, message_id, seen_message_ids):
                recipient.Delete(message_id, deleted=deleted, seen_message_ids=seen_message_ids)

            # create delete request
            log.info("Deleting {} from {}".format(message_id, self.display_address))
            if len(messages) > 0:
                delete = etree.Element("{%s}DeleteItem" % MNS, DeleteType="SoftDelete")
                item_ids = etree.SubElement(delete, "{%s}ItemIds" % MNS)
                for message in messages:
                    item_ids.append(message.ToXML())

                # send the request
                response = self.account.SendRequest(delete, impersonate=self.address)
                log.info("Successfully deleted {} from {}".format(message_id, self.display_address))
            else:
                log.info("Message {} not found for {}".format(message_id, self.display_address))

        return deleted

    def Restore(self, message_id, restored=None, seen_message_ids=None):
        if seen_message_ids is None:
            seen_message_ids = { message_id: True }

        # don't restore to the same address twice
        if restored is None:
            restored = {}
        if self.group is None:
            if self.address in restored:
                return
            restored[self.address] = True

        # restore to the group owner's mailbox
        if self.mailbox_type == "GroupMailbox":
            owner = self.GetOwner()
            if owner is not None:
                owner.Restore(message_id, restored=restored, seen_message_ids=seen_message_ids)

        # restore to all members of distribution list
        elif self.mailbox_type == "PublicDL":
            members = self.Expand()
            for member in members:
                member.Restore(message_id, restored=restored, seen_message_ids=seen_message_ids)

        # restore message from mailbox
        else:
            # find recoverable messages with message_id
            messages = self.RecoverableItems.Find(message_id)

            # restore message to anyone the message was forwarded to
            for recipient in self.FindRecipients(messages, message_id, seen_message_ids):
                recipient.Restore(message_id, restored=restored, seen_message_ids=seen_message_ids)

            # create restore request
            log.info("Restoring {} to {}".format(message_id, self.display_address))
            if len(messages) > 0:
                restore = etree.Element("{%s}MoveItem" % MNS)
                to_folder = etree.SubElement(restore, "{%s}ToFolderId" % MNS)
                to_folder.append(DistinguishedFolder(self, "inbox").ToXML())
                items = etree.SubElement(restore, "{%s}ItemIds" % MNS)
                for message in messages:
                    items.append(message.ToXML())

                # send the request
                response = self.account.SendRequest(restore, impersonate=self.address)
                log.info("Successfully restored {} to {}".format(message_id, self.display_address))
            else:
                log.info("Message {} not found for {}".format(message_id, self.display_address))

        return restored

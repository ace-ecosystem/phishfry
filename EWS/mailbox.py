from .errors import MessageNotFound
from .folder import Folder, DistinguishedFolder
from lxml import etree
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from .restriction import Restriction

class Mailbox():
    def __init__(self, session, xml, group=None):
        self.session = session
        self.group = group
        self.xml = xml

    @property
    def address(self):
        return self.xml.find("{%s}EmailAddress" % TNS).text

    @property
    def mailbox_type(self):
        return self.xml.find("{%s}MailboxType" % TNS).text

    @property
    def messages(self):
        # create find folder request
        find_folder = etree.Element("{%s}FindFolder" % MNS, Traversal="Shallow")

        # add folder shape
        folder_shape = etree.SubElement(find_folder, "{%s}FolderShape" % MNS)
        base_shape = etree.SubElement(folder_shape, "{%s}BaseShape" % TNS)
        base_shape.text = "IdOnly"

        # add restriction for DisplayName=AllItems
        find_folder.append(Restriction("folder:DisplayName", "AllItems"))

        # add parent folder to search in
        parent_folder = etree.SubElement(find_folder, "{%s}ParentFolderIds" % MNS)
        parent_folder.append(DistinguishedFolder(self, "root").xml)

        # send the request
        response = self.session.SendRequest(find_folder, impersonate=self.address)

        return Folder(self, response.find(".//{%s}FolderId" % TNS))

    @property
    def deleted_messages(self):
        return DistinguishedFolder(self, "recoverableitemsdeletions")

    def Delete(self, message_id):
        # find all messages with message_id
        messages = self.messages.Find(message_id)

        # throw exception if message not found
        if len(messages) == 0:
            raise MessageNotFound("Message nott found.")

        # create delete request
        delete = etree.Element("{%s}DeleteItem" % MNS, DeleteType="SoftDelete")

        # add all messages to delete request
        items = etree.SubElement(delete, "{%s}ItemIds" % MNS)
        for message in messages:
            items.append(message.xml)

        # send the request
        response = self.session.SendRequest(delete, impersonate=self.address)

    def Restore(self, message_id):
        # find all messages with message_id
        messages = self.deleted_messages.Find(message_id)

        # throw exception if message not found
        if len(messages) == 0:
            raise MessageNotFound("Message not found.")

        # create restore request
        restore = etree.Element("{%s}MoveItem" % MNS)

        # add restore destination
        to_folder = etree.SubElement(restore, "{%s}ToFolderId" % MNS)
        to_folder.append(DistinguishedFolder(self, "inbox").xml)

        # add all messages to restore request
        items = etree.SubElement(restore, "{%s}ItemIds" % MNS)
        for message in messages:
            items.append(message.xml)

        # send the request
        response = self.session.SendRequest(restore, impersonate=self.address)

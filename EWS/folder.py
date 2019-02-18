from lxml import etree
from .message import Message
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from .restriction import Restriction

class Folder():
    def __init__(self, mailbox, xml):
        self.mailbox = mailbox
        self.xml = xml
        if self.mailbox.group is None:
            self.xml.append(self.mailbox.xml)
        else:
            self.xml.append(self.mailbox.group)

    @property
    def session(self):
        return self.mailbox.session

    def Find(self, message_id):
        # create find item request
        find_item = etree.Element("{%s}FindItem" % MNS, Traversal="Shallow")

        # add item shape
        item_shape = etree.SubElement(find_item, "{%s}ItemShape" % MNS)
        base_shape = etree.SubElement(item_shape, "{%s}BaseShape" % TNS)
        base_shape.text = "IdOnly"

        # add restriction for message_id
        find_item.append(Restriction("message:InternetMessageId", message_id))

        # add parent folder to search in
        parent_folder = etree.SubElement(find_item, "{%s}ParentFolderIds" % MNS)
        parent_folder.append(self.xml)

        # send the request
        response = self.session.SendRequest(find_item, impersonate=self.mailbox.address)

        # return all found messages
        messages = []
        for message in response.findall(".//{%s}ItemId" % TNS):
            messages.append(Message(self, message))
        return messages

class DistinguishedFolder(Folder):
    def __init__(self, mailbox, name):
        Folder.__init__(self, mailbox, etree.Element("{%s}DistinguishedFolderId" % TNS, Id=name))

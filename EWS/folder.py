from lxml import etree
from .message import Message
from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from .restriction import Restriction, IsEqualTo, Contains, Or

class Folder():
    def __init__(self, mailbox, xml):
        self.mailbox = mailbox
        self.folder_id = xml.get("Id")
        self.change_key = xml.get("ChangeKey")

    def ToXML(self):
        # create folder element
        folder = etree.Element("{%s}FolderId" % TNS, Id=self.folder_id, ChangeKey=self.change_key)

        # add mailbox reference
        if self.mailbox.group is None:
            folder.append(self.mailbox.ToXML())
        else:
            folder.append(self.mailbox.group.ToXML())

        # return the folder element
        return folder

    @property
    def account(self):
        return self.mailbox.account

    def Find(self, message_id):
        # create find item request
        find_item = etree.Element("{%s}FindItem" % MNS, Traversal="Shallow")

        # add item shape
        item_shape = etree.SubElement(find_item, "{%s}ItemShape" % MNS)
        base_shape = etree.SubElement(item_shape, "{%s}BaseShape" % TNS)
        base_shape.text = "IdOnly"

        # add additional properties we want returned
        additional_properties = etree.SubElement(item_shape, "{%s}AdditionalProperties" % TNS)
        etree.SubElement(additional_properties, "{%s}FieldURI" % TNS, FieldURI="message:InternetMessageId")

        # add restriction for message_id
        find_item.append(Restriction(Or(IsEqualTo("message:InternetMessageId", message_id), Contains("message:References", message_id))))

        # add parent folder to search in
        parent_folder = etree.SubElement(find_item, "{%s}ParentFolderIds" % MNS)
        parent_folder.append(self.ToXML())

        # send the request
        response = self.account.SendRequest(find_item, impersonate=self.mailbox.address)

        # get list of messages in response
        response_messages = response.findall(".//{%s}Message" % TNS)

        # return message objects
        messages = []
        for message in response_messages:
            messages.append(Message(self.mailbox, message))
        return messages

class DistinguishedFolder(Folder):
    def __init__(self, mailbox, name):
        self.mailbox = mailbox
        self.folder_id = name

    def ToXML(self):
        # create folder element
        folder = etree.Element("{%s}DistinguishedFolderId" % TNS, Id=self.folder_id)

        # add mailbox reference
        if self.mailbox.group is None:
            folder.append(self.mailbox.ToXML())
        else:
            folder.append(self.mailbox.group.ToXML())

        # return the folder element
        return folder

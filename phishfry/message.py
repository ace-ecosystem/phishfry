from .namespaces import ENS, MNS, SNS, TNS, NSMAP
from lxml import etree

class Message():
    def __init__(self, mailbox, xml):
        self.mailbox = mailbox
        item_id_element = xml.find("{%s}ItemId" % TNS)
        self.item_id = item_id_element.get("Id")
        self.message_id = xml.find("{%s}InternetMessageId" % TNS).text

    def ToXML(self):
        # create item element
        item = etree.Element("{%s}ItemId" % TNS, Id=self.item_id)

        # Don't add 'Mailbox' element as it is not a valid child element
        #    of the ItemId XML element.

        # # add mailbox reference
        # if self.mailbox.group is None:
        #     item.append(self.mailbox.ToXML())
        # else:
        #     item.append(self.mailbox.group.ToXML())

        # return the item element
        return item

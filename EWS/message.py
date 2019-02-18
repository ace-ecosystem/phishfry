class Message():
    def __init__(self, folder, xml):
        self.folder = folder
        self.xml = xml
        if self.folder.mailbox.group is None:
            self.xml.append(self.folder.mailbox.xml)
        else:
            self.xml.append(self.folder.mailbox.group)

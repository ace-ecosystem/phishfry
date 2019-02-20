class RemediationResult(object):
    def __init__(self, mailbox_type):
        self.mailbox_type = mailbox_type
        self.success = True
        self.message = None
        self.owner = None
        self.members = []
        self.forwards = []

import logging

log = logging.getLogger(__name__)

class RemediationResult(object):
    def __init__(self, address, message_id, mailbox_type, action, success=True, message=None):
        self.address = address
        self.message_id = message_id
        self.mailbox_type = mailbox_type
        self.success = success
        self.message = message
        self.owner = None
        self.members = []
        self.forwards = []
        self.action = action

    def result(self, message, success=False):
        log.info(message)
        self.success = success
        self.message = message

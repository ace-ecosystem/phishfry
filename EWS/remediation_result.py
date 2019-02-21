import logging

log = logging.getLogger(__name__)

class RemediationResult(object):
    def __init__(self, mailbox_type, success=True, message=None):
        self.mailbox_type = mailbox_type
        self.success = success
        self.message = message
        self.owner = None
        self.members = []
        self.forwards = []

    def result(self, message, success=False):
        log.info(message)
        self.success = success
        self.message = message

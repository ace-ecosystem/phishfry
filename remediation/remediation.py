#!/usr/bin/env python3
from exchangelib import Account, Configuration, Credentials, IMPERSONATION
from exchangelib.ewsdatetime import EWSTimeZone
from exchangelib.errors import ErrorItemNotFound, ErrorNonExistentMailbox, ErrorNameResolutionNoResults
from exchangelib.util import PrettyXmlHandler

class RemediationAccount(Account):
    def __init__(self, server, username, password):
        self.username = username
        credentials = Credentials(username=username, password=password)
        self.config = Configuration(server=server, credentials=credentials)
        self.timezone = EWSTimeZone.timezone("UTC")
        Account.__init__(self, primary_smtp_address=username, config=self.config, access_type=IMPERSONATION, default_timezone=self.timezone)

    # returns account for impersonated username
    def impersonate(self, address):
        return Account(primary_smtp_address=address, config=self.config, access_type=IMPERSONATION, default_timezone=self.timezone)

    # resolves username into {address:mailbox} dictionary
    def resolve_name(self, address, resolved_addresses=None):
        # do not resolve the same address twice
        if resolved_addresses is None:
            resolved_addresses = {}
        if address in resolved_addresses:
            return {}
        resolved_addresses[address] = True

        # resolve address to mailboxes
        mailboxes = self.protocol.resolve_names(["smtp:{}".format(address)])

        results = {}
        for mailbox in mailboxes:
            # recursively resolve the mailbox if it is a distribution list
            if mailbox.mailbox_type == "PublicDL":
                try:
                    members = self.protocol.expand_dl(mailbox.email_address)
                    for member in members:
                        results.update(self.resolve_name(member.email_address, resolved_addresses=resolved_addresses))
                except ErrorNameResolutionNoResults:
                    pass

            # add mailbox to results
            else:
                results[mailbox.email_address] = mailbox

        return results

    # deletes all messages with message_id from the recipient's mailbox
    def delete(self, recipient, message_id):
        # search recipient's AllItems folder for the message
        account = self.impersonate(recipient)
        all_items = account.root.glob("AllItems").folders[0]
        items = all_items.filter(message_id=message_id)

        # raise item not found error when message is not in the AllItems folder
        if len(items) == 0:
            raise ErrorItemNotFound("Message {} not found.".format(message_id))

        # move all found messages into the recoverable items folder
        for item in items:
            item.soft_delete()

    # restores all messages with message id from the recipients recoverable items folder
    def restore(self, recipient, message_id):
        # search recipient's recoverable items folder for the message
        account = self.impersonate(recipient)
        items = account.recoverable_items_deletions.filter(message_id=message_id)

        # raise item not found error when message is not in the recoverable items folder
        if len(items) == 0:
            raise ErrorItemNotFound("Message {} not found.".format(message_id))

        # move all found items back into the inbox
        for item in items:
            item.move(account.inbox)

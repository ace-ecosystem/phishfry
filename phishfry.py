#!/usr/bin/env python3
from exchangelib import Account, Configuration, Credentials, IMPERSONATION
from exchangelib.ewsdatetime import EWSTimeZone
from exchangelib.errors import ErrorItemNotFound, ErrorNonExistentMailbox
from exchangelib.indexed_properties import EmailAddress
from exchangelib.util import PrettyXmlHandler
import logging
import os.path
import sys
import traceback

# helper class for easy phish remediation
class PhishFry:
    # Constructor
    # server - the address of the exchange server
    # credentials - list of tuple containing username and password e.g. [(username, password)]
    def __init__(self, server, credentials):
        self.server = server
        self.credentials = []
        self.timezone = EWSTimeZone.timezone("UTC")
        for username,password in credentials:
            self.credentials.append(Credentials(username=username, password=password))

    def resolve_name(self, address):
        """ Resolves an address to a Mailbox
        :param address: address to resolve
        :return: Mailbox for the address
        """
        for credentials in self.credentials:
            try:
                config = Configuration(server=self.server, credentials=credentials)
                account = Account(primary_smtp_address=credentials.username, config=config, autodiscover=False, access_type=IMPERSONATION, default_timezone=self.timezone)
                mailboxes = account.protocol.resolve_names(["smtp:{}".format(address)])
                if len(mailboxes) > 0:
                    return mailboxes[0]

            # ignore non existent mailbox cause the mailbox might exist on another tenate
            except ErrorNonExistentMailbox:
                pass

        # now throw non existent mailbox because the mailbox was not on any tenate
        raise ErrorNonExistentMailbox('The SMTP address has no mailbox associated with it')

    def expand_distribution_list(self, distribution_list):
        """ Expands a distribution list into list of member mailboxes
        :param distribution_list: Mailbox of the distribution list to expand
        :return: List of member Mailboxes in the distribution list
        """
        for credentials in self.credentials:
            try:
                config = Configuration(server=self.server, credentials=credentials)
                account = Account(primary_smtp_address=credentials.username, config=config, autodiscover=False, access_type=IMPERSONATION, default_timezone=self.timezone)
                mailboxes = account.protocol.expand_dl(distribution_list)
                return mailboxes

            # ignore non existent mailbox cause the mailbox might exist on another tenate
            except ErrorNonExistentMailbox:
                pass

        # now throw non existent mailbox because the mailbox was not on any tenate
        raise ErrorNonExistentMailbox('The SMTP address has no mailbox associated with it')

    def resolve(self, address, resolved_addresses={}):
        """ Recursively resolves an address to all member addresses
        :param address: address to resolve
        :return: dictionary containing all member addresses
        """

        # do not resolve the same address twice
        if address in resolved_addresses:
            return {}
        resolved_addresses[address] = True

        # resolve the address to a mailbox
        try:
            mailbox = self.resolve_name(address)
        except ErrorNonExistentMailbox:
            # return empty set when mailbox doesn't exist
            return {}

        # expand the mailbox if it is a distribution list
        if mailbox.mailbox_type == "PublicDL":
            try:
                members = self.expand_distribution_list(mailbox.email_address)
            except ErrorNonExistentMailbox:
                # return empty set when mailbox doesn't exist
                return {}

            addresses = {}
            for member in members:
                addresses.update(self.resolve(member.email_address, resolved_addresses=resolved_addresses))
            return addresses
        
        # return the resolved mailbox if not a distribution list
        return { mailbox.email_address: mailbox }

    # deletes all messages with message_id from the recipient's mailbox
    def delete(self, recipient, message_id):
        for credentials in self.credentials:
            try:
                # search recipient's AllItems folder for the message
                config = Configuration(server=self.server, credentials=credentials)
                account = Account(primary_smtp_address=recipient, config=config, autodiscover=False, access_type=IMPERSONATION, default_timezone=self.timezone)
                all_items = account.root.glob("AllItems").folders[0]
                items = all_items.filter(message_id=message_id)

                # raise item not found error when message is not in the recoverable items folder
                if len(items) == 0:
                    raise ErrorItemNotFound("Message {} not found.".format(message_id))

                # move all found messages into the recoverable items folder
                for item in items:
                    item.soft_delete()

                # success
                return

            # ignore non existent mailbox cause the mailbox might exist on another tenate
            except ErrorNonExistentMailbox:
                pass

        # now throw non existent mailbox because the mailbox was not on any tenate
        raise ErrorNonExistentMailbox('The SMTP address has no mailbox associated with it')

    # restores all messages with message id from the recipients recoverable items folder
    def restore(self, recipient, message_id):
        for credentials in self.credentials:
            try:
                # search recipient's recoverable items folder for the message
                config = Configuration(server=self.server, credentials=credentials)
                account = Account(primary_smtp_address=recipient, config=config, autodiscover=False, access_type=IMPERSONATION, default_timezone=self.timezone)
                items = account.recoverable_items_deletions.filter(message_id=message_id)

                # raise item not found error when message is not in the recoverable items folder
                if len(items) == 0:
                    raise ErrorItemNotFound("Message {} not found.".format(message_id))

                # move all found items back into the inbox
                for item in items:
                    item.move(account.inbox)

                # success
                return

            # ignore non existent mailbox cause the mailbox might exist on another tenate
            except ErrorNonExistentMailbox:
                pass

        # now throw non existent mailbox because the mailbox was not on any tenate
        raise ErrorNonExistentMailbox('The SMTP address has no mailbox associated with it')

# command line mode
if __name__ == "__main__":
    if (len(sys.argv) == 3 and sys.argv[1] == "resolve") or (len(sys.argv) == 4 and (sys.argv[1] == "delete" or sys.argv[1] == "restore")):
        # show ews debug messages
        #logging.basicConfig(level=logging.DEBUG, handlers=[PrettyXmlHandler()])

        # initialize phishfry
        credentials = []
        creds_path = os.path.join(os.path.dirname(sys.argv[0]), "credentials")
        with open(creds_path, "r") as fp:
            for line in fp:
                line.strip()
                if line != "" and not line.startswith("#"):
                    username, password = line.split(":")
                    credentials.append((username, password))
        phishfry = PhishFry("outlook.office365.com", credentials)

        try:
            # resolve the address to all members mailbox addresses
            print("resolving {}".format(sys.argv[2]))
            addresses = phishfry.resolve(sys.argv[2])

            # delete message from every address
            if sys.argv[1] == "delete":
                for address in addresses:
                    try:
                        print("deleting {} from {}".format(sys.argv[3], address))
                        phishfry.delete(address, sys.argv[3])
                        print("message deleted")
                    except Exception as e:
                        print(e)

            # restore message to every address
            elif sys.argv[1] == "restore":
                for address in addresses:
                    try:
                        print("restoring {} to {}".format(sys.argv[3], address))
                        phishfry.restore(address, sys.argv[3])
                        print("message restored")
                    except Exception as e:
                        print(e)

            # list the resolved mailboxes
            elif sys.argv[1] == "resolve":
                for address in addresses:
                    print(addresses[address])

        except Exception as e:
            print(e)
            traceback.print_exc()

    else:
        print("usage")
        print("{} delete email_address message_id".format(sys.argv[0]))
        print("{} restore email_address message_id".format(sys.argv[0]))
        print("{} resolve email_address".format(sys.argv[0]))

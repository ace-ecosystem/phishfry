#!/usr/bin/env python3
import argparse
import logging
import os.path
from remediation import RemediationAccount
import sys

# global vars
accounts = []

# load accounts from config file
def load_accounts():
    with open(args.config, "r") as fp:
        for line in fp:
            line.strip()
            if line != "" and not line.startswith("#"):
                server, username, password = line.split(":", 2)
                accounts.append(RemediationAccount(server, username, password))

# delete action
def delete():
    for account in accounts:
        # find all recipients
        recipients = account.resolve_name(args.recipient)

        # delete message from all recipients mailboxes
        for recipient in recipients:
            print("deleting {} from {}".format(args.message-id, recipient))
            try:
                account.delete(recipient, args.message_id)
                print("message deleted")
            except Exception as e:
                print(e)

# restore action
def restore():
    for account in accounts:
        # find all recipients
        recipients = account.resolve_name(args.recipient)

        # restore message to all recipients mailboxes
        for recipient in recipients:
            print("restoring {} for {}".format(args.message_id, recipient))
            try:
                account.restore(recipient, args.message_id)
                print("message restored")
            except Exception as e:
                print(e)

# resolve action
def resolve():
    for account in accounts:
        # find all recipients
        recipients = account.resolve_name(args.recipient)
        for recipient in recipients:
            print(recipients[recipient])

# global args
parser = argparse.ArgumentParser()
default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "credentials")
parser.add_argument("-c", dest="config", nargs="?", default=default_config_path, help="specify config path")
parser.add_argument("-v", dest="verbose", help="display verbose output", action="store_true")
subparsers = parser.add_subparsers(dest="action")

# delete args
delete_parser = subparsers.add_parser("delete", help="Delete a message from a recipient's mailbox.")
delete_parser.add_argument('recipient', help="Email address of the recipient")
delete_parser.add_argument('message_id', help="Message ID of the message")
delete_parser.set_defaults(func=delete)

# restore args
restore_parser = subparsers.add_parser("restore", help="Restore a message to a recipient's mailbox.")
restore_parser.add_argument('recipient', help="Email address of the recipient")
restore_parser.add_argument('message_id', help="Message ID of the message")
restore_parser.set_defaults(func=restore)

# resolve action
restore_parser = subparsers.add_parser("resolve", help="Display all mailboxes for a recipient.")
restore_parser.add_argument('recipient', help="Email address of the recipient")
restore_parser.set_defaults(func=resolve)

# parse args
args = parser.parse_args()

# execute action
if args.action:
    # show ews debug messages
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[PrettyXmlHandler()])

    # load accounts
    load_accounts()

    # execute the action
    args.func()

# print help if no action given
else:
    parser.print_help()

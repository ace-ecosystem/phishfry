#!/usr/bin/env python3
import argparse
from configparser import ConfigParser
import EWS
import logging
import os.path

# global vars
accounts = []
config = ConfigParser()

def get_config_var(section, key, default=None):
    if section in config and key in config[section] and config[section][key]:
        return config[section][key]
    elif default is not None:
        return default
    raise Exception("Missing required config variable config[{}][{}]".format(section, key))


# load ews accounts from config.ini
def load_accounts():
    config.read(args.config)
    timezone = get_config_var("DEFAULT", "timezone", default="UTC")

    for section in config.sections():
        server = get_config_var(section, "server", default="outlook.office365.com")
        version = get_config_var(section, "version", default="Exchange2016")
        user = get_config_var(section, "user")
        password = get_config_var(section, "pass")
        accounts.append(EWS.Account(user, password, server=server, version=version, timezone=timezone))

# delete action
def delete():
    for account in accounts:
        try:
            mailbox = account.GetMailbox(args.recipient)
            deleted = mailbox.Delete(args.message_id)
            logging.info(deleted)
            return

        # ignore mailbox not found error since it might exist on another account
        except EWS.MailboxNotFound:
            pass

    # mailbox not found on any account
    logging.error("No mailbox found for {}".format(args.recipient))

# restore action
def restore():
    for account in accounts:
        try:
            mailbox = account.GetMailbox(args.recipient)
            restored = mailbox.Restore(args.message_id)
            logging.info(restored)
            return

        # ignore mailbox not found error since it might exist on another account
        except EWS.MailboxNotFound:
            pass

    # mailbox not found on any account
    logging.error("No mailbox found for {}".format(args.recipient))

# resolve action
def resolve():
    for account in accounts:
        try:
            mailbox = account.GetMailbox(args.recipient)
            logging.info({"address": mailbox.address, "type": mailbox.mailbox_type})
            return

        # ignore mailbox not found error since it might exist on another account
        except EWS.MailboxNotFound:
            pass

    # mailbox not found on any account
    logging.error("No mailbox found for {}".format(args.recipient))


# global args
parser = argparse.ArgumentParser()
default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini")
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
    # init logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    # load accounts
    load_accounts()

    # execute the action
    args.func()

# print help if no action given
else:
    parser.print_help()

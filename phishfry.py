#!/usr/bin/env python3
import argparse
from configparser import ConfigParser
import EWS
import logging
import os.path

# global vars
sessions = []
config = ConfigParser()

def get_config_var(section, key, default=None):
    if section in config and key in config[section] and config[section][key]:
        return config[section][key]
    elif default is not None:
        return default
    raise Exception("Missing required config variable config[{}][{}]".format(section, key))


# create ews sessions from each account in the config file
def load_accounts():
    config.read(args.config)
    timezone = get_config_var("DEFAULT", "timezone", default="UTC")

    for section in config.sections():
        server = get_config_var(section, "server", default="outlook.office365.com")
        version = get_config_var(section, "version", default="Exchange2016")
        user = get_config_var(section, "user")
        password = get_config_var(section, "pass")
        sessions.append(EWS.Session(user, password, server=server, version=version, timezone=timezone))

# delete action
def delete():
    # try all sessions
    for session in sessions:
        try:
            # find all mailboxes the recipient address delivers to
            mailboxes = session.Resolve(args.recipient)

            # delete message from all mailboxes
            for mailbox in mailboxes:
                logging.info("deleting {} from {}".format(args.message_id, mailbox.address))
                try:
                    mailbox.Delete(args.message_id)
                    logging.info("message deleted")
                except EWS.MessageNotFound:
                    logging.info("message not found")

            # success
            return

        # ignore mailbox not found error since mailbox may resolve on a different session
        except EWS.MailboxNotFound:
            pass

    # we didn't find the mailbox on any session
    logging.error("Mailbox not found")

# restore action
def restore():
    # try all sessions
    for session in sessions:
        try:
            # find all mailboxes the recipient address delivers to
            mailboxes = session.Resolve(args.recipient)

            # restore message to all mailboxes
            for mailbox in mailboxes:
                logging.info("restoring {} to {}".format(args.message_id, mailbox.address))
                try:
                    mailbox.Restore(args.message_id)
                    logging.info("message restored")
                except EWS.MessageNotFound:
                    logging.info("message not found")

            # success
            return

        # ignore mailbox not found error since mailbox may resolve on a different session
        except EWS.MailboxNotFound:
            pass

    # we didn't find the mailbox on any session
    logging.error("Mailbox not found")

# resolve action
def resolve():
    # try all sessions
    for session in sessions:
        try:
            # find all mailboxes the recipient address delivers to
            mailboxes = session.Resolve(args.recipient)

            # print all resolved addresses
            for mailbox in mailboxes:
                logging.info(mailbox.address)

        # ignore mailbox not found error since mailbox may resolve on a different session
        except EWS.MailboxNotFound:
            pass

    # we didn't find the mailbox on any session
    logging.error("Mailbox not found")


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

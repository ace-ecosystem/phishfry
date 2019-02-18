#!/usr/bin/env python3
import argparse
from configparser import ConfigParser
import logging
import os.path
import EWS

# global vars
sessions = []
config = ConfigParser()

def GetConfigVar(section, key, default=None):
    if section in config and key in config[section] and config[section][key]:
        return config[section][key]
    elif default is not None:
        return default
    raise Exception("Missing required config variable config[{}][{}]".format(section, key))


# create ews sessions from each account in the config file
def load_accounts():
    config.read(args.config)
    timezone = GetConfigVar("DEFAULT", "timezone", default="UTC")

    for section in config.sections():
        server = GetConfigVar(section, "server", default="outlook.office365.com")
        version = GetConfigVar(section, "version", default="Exchange2016")
        user = GetConfigVar(section, "user")
        password = GetConfigVar(section, "pass")
        sessions.append(EWS.Session(user, password, server=server, version=version, timezone=timezone))

# delete action
def delete():
    for session in sessions:
        # find all mailboxes the recipient address delivers to
        mailboxes = session.Resolve(args.recipient)

        # delete message from all mailboxes
        for address in mailboxes:
            print("deleting {} from {}".format(args.message_id, address))
            try:
                mailboxes[address].Delete(args.message_id)
                print("message deleted")
            except Exception as e:
                print(e)

# restore action
def restore():
    for session in sessions:
        # find all mailboxes the recipient address delivers to
        mailboxes = session.Resolve(args.recipient)

        # restore message to all mailboxes
        for address in mailboxes:
            print("restore {} to {}".format(args.message_id, address))
            try:
                mailboxes[address].Restore(args.message_id)
                print("message restored")
            except Exception as e:
                print(e)

# resolve action
def resolve():
    for session in sessions:
        # find all mailboxes the recipient address delivers to
        mailboxes = session.Resolve(args.recipient)

        # print all resolved addresses
        for address in mailboxes:
            print(address)

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
    # show ews debug messages
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # load accounts
    load_accounts()

    # execute the action
    args.func()

# print help if no action given
else:
    parser.print_help()

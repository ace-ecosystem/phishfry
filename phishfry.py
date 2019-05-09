#!/usr/bin/env python3
import argparse
from configparser import ConfigParser
import EWS
import logging
import os.path
import time

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

# remove action
def remove():
    for account in accounts:
        results = account.Remove(args.recipient, args.message_id)

        # if the address resolved on this account then stop
        if results[args.recipient].mailbox_type != "Unknown":
            return

    # report error if mailbox not found on any account
    logging.error("Mailbox not found")

# restore action
def restore():
    for account in accounts:
        results = account.Restore(args.recipient, args.message_id)

        # if the address resolved on this account then stop
        if results[args.recipient].mailbox_type != "Unknown":
            return

    # report error if mailbox not found on any account
    logging.error("Mailbox not found")

# rules action
def rules():
    for account in accounts:
        results = account.GetInboxRules(args.recipient)

        # if the address resolved on this account then stop
        if results:
            return

    # report error if mailbox not found on any account
    logging.error("Mailbox not found")


# global args
parser = argparse.ArgumentParser()
default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini")
parser.add_argument("-c", dest="config", nargs="?", default=default_config_path, help="specify config path")
parser.add_argument("-v", dest="verbose", help="display verbose output", action="store_true")
subparsers = parser.add_subparsers(dest="action")

# remove args
remove_parser = subparsers.add_parser("remove", help="Remove a message from a recipient's mailbox.")
remove_parser.add_argument('recipient', help="Email address of the recipient")
remove_parser.add_argument('message_id', help="Message ID of the message")
remove_parser.set_defaults(func=remove)

# restore args
restore_parser = subparsers.add_parser("restore", help="Restore a message to a recipient's mailbox.")
restore_parser.add_argument('recipient', help="Email address of the recipient")
restore_parser.add_argument('message_id', help="Message ID of the message")
restore_parser.set_defaults(func=restore)

# rules args
rules_parser = subparsers.add_parser("rules", help="Get the inbox rules for a recipient.")
rules_parser.add_argument('recipient', help="Email address of the recipient")
rules_parser.set_defaults(func=rules)

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
    start_time = time.time()
    args.func()
    logging.info("took {}s".format(time.time() - start_time))

# print help if no action given
else:
    parser.print_help()

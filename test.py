#!/usr/bin/env python3
from configparser import ConfigParser
import EWS
import unittest

config = ConfigParser()
config.read("/opt/phishfry/config.ini")
user = config["test"]["user"]
password = config["test"]["pass"]
account = EWS.Account(user, password)

class TestEWS(unittest.TestCase):
    def test_remediate(self):
        mailbox = account.GetMailbox("test@integraldefense.com")

        try:
            mailbox.Delete("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
            deleted = True
        except EWS.MessageNotFound:
            mailbox.Restore("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
            deleted = False

        if deleted:
            mailbox.Restore("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
        else:
            mailbox.Delete("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")

    def test_resolve_alias(self):
        mailbox = account.GetMailbox("test@integraldefense.onmicrosoft.com")
        self.assertEqual(mailbox.address, "test@integraldefense.com")

    def test_expand_distribution_list(self):
        mailbox = account.GetMailbox("testemaillist@integraldefense.com")
        members = mailbox.Expand()
        self.assertEqual(len(members), 2)

    def test_get_group_owner(self):
        mailbox = account.GetMailbox("testinggroupemail@integraldefense.com")
        owner = mailbox.GetOwner()
        self.assertNotEqual(owner, None)

if __name__ == '__main__':
    unittest.main(verbosity=2)

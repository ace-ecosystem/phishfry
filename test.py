#!/usr/bin/env python3
from configparser import ConfigParser
import EWS
import unittest

config = ConfigParser()
config.read("/opt/phishfry/config.ini")
user = config["test"]["user"]
password = config["test"]["pass"]
session = EWS.Session(user, password)

class TestEWS(unittest.TestCase):
    def test_remediate(self):
        mailboxes = session.Resolve("test@integraldefense.com")
        self.assertEqual(len(mailboxes), 1)
        mailbox = mailboxes[0]

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
        mailboxes = session.Resolve("test@integraldefense.onmicrosoft.com")
        self.assertEqual(len(mailboxes), 1)
        mailbox = mailboxes[0]
        self.assertEqual(mailbox.address, "test@integraldefense.com")

    def test_resolve_distribution_list(self):
        mailboxes = session.Resolve("testemaillist@integraldefense.com")
        self.assertEqual(len(mailboxes), 2)

    def test_remediate_group(self):
        mailboxes = session.Resolve("testinggroupemail@integraldefense.com")
        self.assertEqual(len(mailboxes), 1)
        mailbox = mailboxes[0]

        try:
            mailbox.Delete("<CAAoaDjRtca44oy9FLPLnawxTSUibJeRhcfbEw1H5_EmcymzNzg@mail.gmail.com>")
            deleted = True
        except EWS.MessageNotFound:
            mailbox.Restore("<CAAoaDjRtca44oy9FLPLnawxTSUibJeRhcfbEw1H5_EmcymzNzg@mail.gmail.com>")
            deleted = False

        if deleted:
            mailbox.Restore("<CAAoaDjRtca44oy9FLPLnawxTSUibJeRhcfbEw1H5_EmcymzNzg@mail.gmail.com>")
        else:
            mailbox.Delete("<CAAoaDjRtca44oy9FLPLnawxTSUibJeRhcfbEw1H5_EmcymzNzg@mail.gmail.com>")

if __name__ == '__main__':
    unittest.main(verbosity=2)

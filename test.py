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
    def test_remediate_forward_to_group(self):
        mailbox = account.GetMailbox("test@integraldefense.com")

        # test deleting email that was forwarded to group
        deleted = mailbox.Delete("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", deleted)
        self.assertTrue(deleted["test@integraldefense.com"])
        self.assertIn("testinggroupemail@integraldefense.com", deleted)
        self.assertTrue(deleted["testinggroupemail@integraldefense.com"])

        # test restoring email that was forwarded to group
        restored = mailbox.Restore("<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", restored)
        self.assertTrue(restored["test@integraldefense.com"])
        self.assertIn("testinggroupemail@integraldefense.com", restored)
        self.assertTrue(restored["testinggroupemail@integraldefense.com"])

    def test_remediate_non_existent_message(self):
        mailbox = account.GetMailbox("test@integraldefense.com")

        # test deleting non existent message
        deleted = mailbox.Delete("<non-existent-message-id>")
        self.assertIn("test@integraldefense.com", deleted)
        self.assertFalse(deleted["test@integraldefense.com"])

        # test restoring non existent message
        restored = mailbox.Restore("non-existent-message-id>")
        self.assertIn("test@integraldefense.com", restored)
        self.assertFalse(restored["test@integraldefense.com"])

    def test_remediate_reply_to_external_mailbox(self):
        mailbox = account.GetMailbox("test@integraldefense.com")

        # test deleting email that was forwarded to group
        deleted = mailbox.Delete("<CAAoaDjQJ3Kor1nZMPJwEN56KK0pBDxyjhJjR-Hgj7ZA85hKy-w@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", deleted)
        self.assertTrue(deleted["test@integraldefense.com"])

        # test restoring email that was forwarded to group
        restored = mailbox.Restore("<CAAoaDjQJ3Kor1nZMPJwEN56KK0pBDxyjhJjR-Hgj7ZA85hKy-w@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", restored)
        self.assertTrue(restored["test@integraldefense.com"])

    def test_resolve_alias(self):
        mailbox = account.GetMailbox("test@integraldefense.onmicrosoft.com")
        self.assertEqual(mailbox.address, "test@integraldefense.com")

    def test_resolve_non_existent_email(self):
        with self.assertRaises(EWS.MailboxNotFound):
            mailbox = account.GetMailbox("non_existent@integraldefense.com")

    def test_expand_distribution_list(self):
        mailbox = account.GetMailbox("testemaillist@integraldefense.com")
        members = mailbox.Expand()
        self.assertEqual(len(members), 2)

    def test_get_group_owner(self):
        mailbox = account.GetMailbox("testinggroupemail@integraldefense.com")
        owner = mailbox.GetOwner()
        self.assertNotEqual(owner, None)
        self.assertEqual(owner.group.address, "testinggroupemail@integraldefense.com")

if __name__ == '__main__':
    unittest.main(verbosity=2)

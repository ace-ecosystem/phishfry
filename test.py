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
        # restore first in case deleted
        account.Restore("test@integraldefense.com", "<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")

        # test deleting email that was forwarded to group
        results = account.Delete("test@integraldefense.com", "<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", results)
        self.assertTrue(results["test@integraldefense.com"].success)
        self.assertIn("testinggroupemail@integraldefense.com", results)
        self.assertTrue(results["testinggroupemail@integraldefense.com"].success)

        # test restoring email that was forwarded to group
        results = account.Restore("test@integraldefense.com", "<CAAoaDjT=8xPVW6e=yyv2eji7rzUMxPwnv6uMJJVzYbFK=LPCVw@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", results)
        self.assertTrue(results["test@integraldefense.com"].success)
        self.assertIn("testinggroupemail@integraldefense.com", results)
        self.assertTrue(results["testinggroupemail@integraldefense.com"].success)

    def test_remediate_non_existent_message(self):
        # restore first in case it is deleted
        account.Restore("test@integraldefense.com", "<non-existent-message-id>")

        # test deleting non existent message
        results = account.Delete("test@integraldefense.com", "<non-existent-message-id>")
        self.assertIn("test@integraldefense.com", results)
        self.assertTrue(results["test@integraldefense.com"].success)
        self.assertEqual(results["test@integraldefense.com"].message, "Message not found")

        # test restoring non existent message
        results = account.Restore("test@integraldefense.com", "<non-existent-message-id>")
        self.assertIn("test@integraldefense.com", results)
        self.assertFalse(results["test@integraldefense.com"].success)
        self.assertEqual(results["test@integraldefense.com"].message, "Message not found")

    def test_remediate_reply_to_external_mailbox(self):
        # restore first in case deleted
        account.Restore("test@integraldefense.com", "<CAAoaDjQJ3Kor1nZMPJwEN56KK0pBDxyjhJjR-Hgj7ZA85hKy-w@mail.gmail.com>")

        # test deleting email that was forwarded to external mailbox
        results = account.Delete("test@integraldefense.com", "<CAAoaDjQJ3Kor1nZMPJwEN56KK0pBDxyjhJjR-Hgj7ZA85hKy-w@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", results)
        self.assertTrue(results["test@integraldefense.com"].success)

        # test restoring email that was forwarded to external mailbox
        results = account.Restore("test@integraldefense.com", "<CAAoaDjQJ3Kor1nZMPJwEN56KK0pBDxyjhJjR-Hgj7ZA85hKy-w@mail.gmail.com>")
        self.assertIn("test@integraldefense.com", results)
        self.assertTrue(results["test@integraldefense.com"].success)

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
        self.assertEqual(owner.group.address, "testinggroupemail@integraldefense.com")

if __name__ == '__main__':
    unittest.main(verbosity=2)

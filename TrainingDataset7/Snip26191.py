def test_send_many(self):
        email1 = EmailMessage(to=["to-1@example.com"])
        email2 = EmailMessage(to=["to-2@example.com"])
        # send_messages() may take a list or an iterator.
        emails_lists = ([email1, email2], iter((email1, email2)))
        for emails_list in emails_lists:
            with self.subTest(emails_list=repr(emails_list)):
                num_sent = mail.get_connection().send_messages(emails_list)
                self.assertEqual(num_sent, 2)
                messages = self.get_mailbox_content()
                self.assertEqual(len(messages), 2)
                self.assertEqual(messages[0]["To"], "to-1@example.com")
                self.assertEqual(messages[1]["To"], "to-2@example.com")
                self.flush_mailbox()
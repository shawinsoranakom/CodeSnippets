def test_single_receiver(self):
        """
        The mail is sent with the correct subject and recipient.
        """
        recipient = "joe@example.com"
        call_command("sendtestemail", recipient)
        self.assertEqual(len(mail.outbox), 1)
        mail_message = mail.outbox[0]
        self.assertEqual(mail_message.subject[0:15], "Test email from")
        self.assertEqual(mail_message.recipients(), [recipient])
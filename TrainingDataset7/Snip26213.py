def test_outbox_not_mutated_after_send(self):
        email = EmailMessage(
            subject="correct subject",
            to=["to@example.com"],
        )
        email.send()
        email.subject = "other subject"
        email.to.append("other@example.com")
        self.assertEqual(mail.outbox[0].subject, "correct subject")
        self.assertEqual(mail.outbox[0].to, ["to@example.com"])
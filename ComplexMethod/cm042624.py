def test_send(self):
        mailsender = MailSender(debug=True)
        mailsender.send(
            to=["test@scrapy.org"],
            subject="subject",
            body="body",
            _callback=self._catch_mail_sent,
        )

        assert self.catched_msg

        assert self.catched_msg["to"] == ["test@scrapy.org"]
        assert self.catched_msg["subject"] == "subject"
        assert self.catched_msg["body"] == "body"

        msg = self.catched_msg["msg"]
        assert msg["to"] == "test@scrapy.org"
        assert msg["subject"] == "subject"
        assert msg.get_payload() == "body"
        assert msg.get("Content-Type") == "text/plain"
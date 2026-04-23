def test_send_utf8(self):
        subject = "sübjèçt"
        body = "bödÿ-àéïöñß"
        mailsender = MailSender(debug=True)
        mailsender.send(
            to=["test@scrapy.org"],
            subject=subject,
            body=body,
            charset="utf-8",
            _callback=self._catch_mail_sent,
        )

        assert self.catched_msg
        assert self.catched_msg["subject"] == subject
        assert self.catched_msg["body"] == body

        msg = self.catched_msg["msg"]
        assert msg["subject"] == subject
        assert msg.get_payload(decode=True).decode("utf-8") == body
        assert msg.get_charset() == Charset("utf-8")
        assert msg.get("Content-Type") == 'text/plain; charset="utf-8"'
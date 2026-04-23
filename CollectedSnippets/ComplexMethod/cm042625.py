def test_send_attach(self):
        attach = BytesIO()
        attach.write(b"content")
        attach.seek(0)
        attachs = [("attachment", "text/plain", attach)]

        mailsender = MailSender(debug=True)
        mailsender.send(
            to=["test@scrapy.org"],
            subject="subject",
            body="body",
            attachs=attachs,
            _callback=self._catch_mail_sent,
        )

        assert self.catched_msg
        assert self.catched_msg["to"] == ["test@scrapy.org"]
        assert self.catched_msg["subject"] == "subject"
        assert self.catched_msg["body"] == "body"

        msg = self.catched_msg["msg"]
        assert msg["to"] == "test@scrapy.org"
        assert msg["subject"] == "subject"

        payload = msg.get_payload()
        assert isinstance(payload, list)
        assert len(payload) == 2

        text, attach = payload
        assert text.get_payload(decode=True) == b"body"
        assert text.get_charset() == Charset("us-ascii")
        assert attach.get_payload(decode=True) == b"content"
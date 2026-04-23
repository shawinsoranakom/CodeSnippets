def test_send_attach_utf8(self):
        subject = "sübjèçt"
        body = "bödÿ-àéïöñß"
        attach = BytesIO()
        attach.write(body.encode("utf-8"))
        attach.seek(0)
        attachs = [("attachment", "text/plain", attach)]

        mailsender = MailSender(debug=True)
        mailsender.send(
            to=["test@scrapy.org"],
            subject=subject,
            body=body,
            attachs=attachs,
            charset="utf-8",
            _callback=self._catch_mail_sent,
        )

        assert self.catched_msg
        assert self.catched_msg["subject"] == subject
        assert self.catched_msg["body"] == body

        msg = self.catched_msg["msg"]
        assert msg["subject"] == subject
        assert msg.get_charset() == Charset("utf-8")
        assert msg.get("Content-Type") == 'multipart/mixed; charset="utf-8"'

        payload = msg.get_payload()
        assert isinstance(payload, list)
        assert len(payload) == 2

        text, attach = payload
        assert text.get_payload(decode=True).decode("utf-8") == body
        assert text.get_charset() == Charset("utf-8")
        assert attach.get_payload(decode=True).decode("utf-8") == body
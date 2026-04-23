def test_cc_headers(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            cc=["foo@example.com"],
            headers={"Cc": "override@example.com"},
        ).message()
        self.assertEqual(message.get_all("Cc"), ["override@example.com"])
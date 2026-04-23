def test_cc_in_headers_only(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"Cc": "foo@example.com"},
        ).message()
        self.assertEqual(message.get_all("Cc"), ["foo@example.com"])
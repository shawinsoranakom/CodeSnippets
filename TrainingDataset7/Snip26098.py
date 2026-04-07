def test_to_in_headers_only(self):
        message = EmailMessage(
            headers={"To": "to@example.com"},
        ).message()
        self.assertEqual(message.get_all("To"), ["to@example.com"])
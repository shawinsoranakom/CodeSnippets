def test_forbid_multi_line_headers_deprecated(self):
        msg = (
            "The internal API forbid_multi_line_headers() is deprecated."
            " Python's modern email API (with email.message.EmailMessage or"
            " email.policy.default) will reject multi-line headers."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
            forbid_multi_line_headers("To", "to@example.com", "ascii")
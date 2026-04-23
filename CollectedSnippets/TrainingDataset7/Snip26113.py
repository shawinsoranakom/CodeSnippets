def test_non_ascii_dns_non_unicode_email(self, mocked_getfqdn):
        delattr(DNS_NAME, "_fqdn")
        email = EmailMessage()
        email.encoding = "iso-8859-1"
        self.assertIn("@xn--p8s937b>", email.message()["Message-ID"])
def test_referer_equal_to_requested_url(self):
        """
        Some bots set the referer to the current URL to avoid being blocked by
        an referer check (#25302).
        """
        self.req.META["HTTP_REFERER"] = self.req.path
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 0)

        # URL with scheme and domain should also be ignored
        self.req.META["HTTP_REFERER"] = "http://testserver%s" % self.req.path
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 0)

        # URL with a different scheme should be ignored as well because bots
        # tend to use http:// in referers even when browsing HTTPS websites.
        self.req.META["HTTP_X_PROTO"] = "https"
        self.req.META["SERVER_PORT"] = 443
        with self.settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_PROTO", "https")):
            BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 0)
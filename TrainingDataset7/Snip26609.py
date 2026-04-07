def test_404_error_reporting(self):
        self.req.META["HTTP_REFERER"] = "/another/url/"
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Broken", mail.outbox[0].subject)
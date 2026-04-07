def test_404_error_reporting_ignored_url(self):
        self.req.path = self.req.path_info = "foo_url/that/does/not/exist"
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 0)
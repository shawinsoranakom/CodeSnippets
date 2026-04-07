def test_referer_equal_to_requested_url_on_another_domain(self):
        self.req.META["HTTP_REFERER"] = "http://anotherserver%s" % self.req.path
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 1)
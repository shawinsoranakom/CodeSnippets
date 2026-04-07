def test_referer_equal_to_requested_url_without_trailing_slash_with_no_append_slash(
        self,
    ):
        self.req.path = self.req.path_info = "/regular_url/that/does/not/exist/"
        self.req.META["HTTP_REFERER"] = self.req.path_info[:-1]
        BrokenLinkEmailsMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 1)
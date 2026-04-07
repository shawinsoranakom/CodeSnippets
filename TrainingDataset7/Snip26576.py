def test_append_slash_slashless_resource(self):
        """
        Matches to explicit slashless URLs should go unmolested.
        """

        def get_response(req):
            return HttpResponse("Here's the text of the web page.")

        request = self.rf.get("/noslash")
        self.assertIsNone(CommonMiddleware(get_response).process_request(request))
        self.assertEqual(
            CommonMiddleware(get_response)(request).content,
            b"Here's the text of the web page.",
        )
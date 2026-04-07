def test_append_slash_have_slash(self):
        """
        URLs with slashes should go unmolested.
        """
        request = self.rf.get("/slash/")
        self.assertIsNone(CommonMiddleware(get_response_404).process_request(request))
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)
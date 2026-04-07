def test_append_slash_leading_slashes(self):
        """
        Paths starting with two slashes are escaped to prevent open redirects.
        If there's a URL pattern that allows paths to start with two slashes, a
        request with path //evil.com must not redirect to //evil.com/ (appended
        slash) which is a schemaless absolute URL. The browser would navigate
        to evil.com/.
        """
        # Use 4 slashes because of RequestFactory behavior.
        request = self.rf.get("////evil.com/security")
        r = CommonMiddleware(get_response_404).process_request(request)
        self.assertIsNone(r)
        response = HttpResponseNotFound()
        r = CommonMiddleware(get_response_404).process_response(request, response)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/%2Fevil.com/security/")
        r = CommonMiddleware(get_response_404)(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/%2Fevil.com/security/")
def test_append_slash_no_redirect_on_POST_in_DEBUG_custom_urlconf(self):
        """
        While in debug mode, an exception is raised with a warning
        when a failed attempt is made to POST to an URL which would normally be
        redirected to a slashed version.
        """
        request = self.rf.get("/customurlconf/slash")
        request.urlconf = "middleware.extra_urls"
        request.method = "POST"
        with self.assertRaisesMessage(RuntimeError, "end in a slash"):
            CommonMiddleware(get_response_404)(request)
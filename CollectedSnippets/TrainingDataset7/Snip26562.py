def test_redirect_exempt(self):
        """
        The middleware does not redirect requests with URL path matching an
        exempt pattern.
        """
        ret = self.process_request("get", "/insecure/page")
        self.assertIsNone(ret)
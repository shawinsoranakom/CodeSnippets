def test_https_good_referer_behind_proxy(self):
        """
        A POST HTTPS request is accepted when USE_X_FORWARDED_PORT=True.
        """
        self._test_https_good_referer_behind_proxy()
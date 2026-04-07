def test_redirect_loop(self):
        """
        Detect a redirect loop if LOGIN_REDIRECT_URL is not correctly set,
        with and without custom parameters.
        """
        self.login()
        msg = (
            "Redirection loop for authenticated user detected. Check that "
            "your LOGIN_REDIRECT_URL doesn't point to a login page."
        )
        with self.settings(LOGIN_REDIRECT_URL=self.do_redirect_url):
            with self.assertRaisesMessage(ValueError, msg):
                self.client.get(self.do_redirect_url)

            url = self.do_redirect_url + "?bla=2"
            with self.assertRaisesMessage(ValueError, msg):
                self.client.get(url)
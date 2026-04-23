def _check_token_present(self, response, csrf_secret=None):
        if csrf_secret is None:
            csrf_secret = TEST_SECRET
        text = str(response.content, response.charset)
        match = re.search('name="csrfmiddlewaretoken" value="(.*?)"', text)
        self.assertTrue(
            match,
            f"Could not find a csrfmiddlewaretoken value in: {text}",
        )
        csrf_token = match[1]
        self.assertMaskedSecretCorrect(csrf_token, csrf_secret)
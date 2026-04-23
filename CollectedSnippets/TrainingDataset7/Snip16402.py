def test_login_successfully_redirects_to_original_URL(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        query_string = "the-answer=42"
        redirect_url = "%s?%s" % (self.index_url, query_string)
        new_next = {REDIRECT_FIELD_NAME: redirect_url}
        post_data = self.super_login.copy()
        post_data.pop(REDIRECT_FIELD_NAME)
        login = self.client.post(
            "%s?%s" % (reverse("admin:login"), urlencode(new_next)), post_data
        )
        self.assertRedirects(login, redirect_url)
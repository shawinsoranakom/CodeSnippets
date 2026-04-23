def test_redirect_with_append_slash_and_query_string(self):
        Redirect.objects.create(
            site=self.site, old_path="/initial/?foo", new_path="/new_target/"
        )
        response = self.client.get("/initial?foo")
        self.assertRedirects(
            response, "/new_target/", status_code=301, target_status_code=404
        )
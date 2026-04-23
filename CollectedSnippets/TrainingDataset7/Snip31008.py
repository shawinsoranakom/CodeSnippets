def test_response_redirect_class(self):
        Redirect.objects.create(
            site=self.site, old_path="/initial/", new_path="/new_target/"
        )
        response = self.client.get("/initial/")
        self.assertEqual(response.status_code, 302)
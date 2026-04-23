def test_redirect(self):
        Redirect.objects.create(
            site=self.site, old_path="/initial", new_path="/new_target"
        )
        response = self.client.get("/initial")
        self.assertRedirects(
            response, "/new_target", status_code=301, target_status_code=404
        )
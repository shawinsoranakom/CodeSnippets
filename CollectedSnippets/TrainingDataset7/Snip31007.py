def test_response_gone_class(self):
        Redirect.objects.create(site=self.site, old_path="/initial/", new_path="")
        response = self.client.get("/initial/")
        self.assertEqual(response.status_code, 403)
def test_response_gone(self):
        """When the redirect target is '', return a 410"""
        Redirect.objects.create(site=self.site, old_path="/initial", new_path="")
        response = self.client.get("/initial")
        self.assertEqual(response.status_code, 410)
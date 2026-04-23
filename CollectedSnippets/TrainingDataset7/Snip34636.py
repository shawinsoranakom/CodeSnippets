def test_external_redirect(self):
        response = self.client.get("/django_project_redirect/")
        self.assertRedirects(
            response, "https://www.djangoproject.com/", fetch_redirect_response=False
        )
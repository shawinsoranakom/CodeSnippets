def test_model_index(self):
        response = self.client.get(reverse("django-admindocs-models-index"))
        self.assertContains(
            response,
            '<h2 id="app-auth">Authentication and Authorization (django.contrib.auth)'
            "</h2>",
            html=True,
        )
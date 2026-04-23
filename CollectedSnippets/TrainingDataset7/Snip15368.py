def test_app_not_found(self):
        response = self.client.get(
            reverse("django-admindocs-models-detail", args=["doesnotexist", "Person"])
        )
        self.assertEqual(response.context["exception"], "App 'doesnotexist' not found")
        self.assertEqual(response.status_code, 404)
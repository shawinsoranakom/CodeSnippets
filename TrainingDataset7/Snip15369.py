def test_model_not_found(self):
        response = self.client.get(
            reverse(
                "django-admindocs-models-detail", args=["admin_docs", "doesnotexist"]
            )
        )
        self.assertEqual(
            response.context["exception"],
            "Model 'doesnotexist' not found in app 'admin_docs'",
        )
        self.assertEqual(response.status_code, 404)
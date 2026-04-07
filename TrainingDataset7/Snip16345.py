def test_app_index_context(self):
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertContains(
            response,
            "<title>Admin_Views administration | Django site admin</title>",
        )
        self.assertEqual(response.context["title"], "Admin_Views administration")
        self.assertEqual(response.context["app_label"], "admin_views")
        # Models are sorted alphabetically by default.
        models = [model["name"] for model in response.context["app_list"][0]["models"]]
        self.assertSequenceEqual(models, sorted(models))
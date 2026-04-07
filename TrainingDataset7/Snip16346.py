def test_app_index_context_reordered(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin2:app_list", args=("admin_views",)))
        self.assertContains(
            response,
            "<title>Admin_Views administration | Django site admin</title>",
        )
        # Models are in reverse order.
        models = [model["name"] for model in response.context["app_list"][0]["models"]]
        self.assertSequenceEqual(models, sorted(models, reverse=True))
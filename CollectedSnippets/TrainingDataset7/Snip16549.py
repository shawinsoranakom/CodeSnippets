def test_model_add(self):
        "Check the never-cache status of a model add page"
        response = self.client.get(reverse("admin:admin_views_fabric_add"))
        self.assertEqual(get_max_age(response), 0)
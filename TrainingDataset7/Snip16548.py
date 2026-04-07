def test_model_index(self):
        "Check the never-cache status of a model index"
        response = self.client.get(reverse("admin:admin_views_fabric_changelist"))
        self.assertEqual(get_max_age(response), 0)
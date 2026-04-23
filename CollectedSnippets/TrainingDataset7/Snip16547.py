def test_app_index(self):
        "Check the never-cache status of an application index"
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertEqual(get_max_age(response), 0)
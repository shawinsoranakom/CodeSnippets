def test_admin_index(self):
        "Check the never-cache status of the main index"
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(get_max_age(response), 0)
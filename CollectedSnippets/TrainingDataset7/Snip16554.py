def test_logout(self):
        "Check the never-cache status of logout view"
        response = self.client.post(reverse("admin:logout"))
        self.assertEqual(get_max_age(response), 0)
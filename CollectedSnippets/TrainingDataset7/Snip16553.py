def test_login(self):
        "Check the never-cache status of login views"
        self.client.logout()
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(get_max_age(response), 0)
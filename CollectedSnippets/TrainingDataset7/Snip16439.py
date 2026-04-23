def test_add(self):
        self.client.force_login(self.adduser)
        url = reverse("admin:admin_views_userproxy_add")
        data = {
            "username": "can_add",
            "password": "secret",
            "date_joined_0": "2019-01-15",
            "date_joined_1": "16:59:10",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProxy.objects.filter(username="can_add").exists())
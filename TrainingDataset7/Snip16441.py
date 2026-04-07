def test_change(self):
        self.client.force_login(self.changeuser)
        data = {
            "password": self.user_proxy.password,
            "username": self.user_proxy.username,
            "date_joined_0": self.user_proxy.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": self.user_proxy.date_joined.strftime("%H:%M:%S"),
            "first_name": "first_name",
        }
        url = reverse("admin:admin_views_userproxy_change", args=(self.user_proxy.pk,))
        response = self.client.post(url, data)
        self.assertRedirects(
            response, reverse("admin:admin_views_userproxy_changelist")
        )
        self.assertEqual(
            UserProxy.objects.get(pk=self.user_proxy.pk).first_name, "first_name"
        )
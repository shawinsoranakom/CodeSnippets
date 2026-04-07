def test_delete(self):
        self.client.force_login(self.deleteuser)
        url = reverse("admin:admin_views_userproxy_delete", args=(self.user_proxy.pk,))
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserProxy.objects.filter(pk=self.user_proxy.pk).exists())
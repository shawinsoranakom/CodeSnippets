def test_xview_func(self):
        user = User.objects.get(username="super")
        response = self.client.head("/xview/func/")
        self.assertNotIn("X-View", response)
        self.client.force_login(self.superuser)
        response = self.client.head("/xview/func/")
        self.assertIn("X-View", response)
        self.assertEqual(response.headers["X-View"], "admin_docs.views.xview")
        user.is_staff = False
        user.save()
        response = self.client.head("/xview/func/")
        self.assertNotIn("X-View", response)
        user.is_staff = True
        user.is_active = False
        user.save()
        response = self.client.head("/xview/func/")
        self.assertNotIn("X-View", response)
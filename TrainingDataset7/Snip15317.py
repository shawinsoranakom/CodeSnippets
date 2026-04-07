def test_xview_class(self):
        user = User.objects.get(username="super")
        response = self.client.head("/xview/class/")
        self.assertNotIn("X-View", response)
        self.client.force_login(self.superuser)
        response = self.client.head("/xview/class/")
        self.assertIn("X-View", response)
        self.assertEqual(response.headers["X-View"], "admin_docs.views.XViewClass")
        user.is_staff = False
        user.save()
        response = self.client.head("/xview/class/")
        self.assertNotIn("X-View", response)
        user.is_staff = True
        user.is_active = False
        user.save()
        response = self.client.head("/xview/class/")
        self.assertNotIn("X-View", response)
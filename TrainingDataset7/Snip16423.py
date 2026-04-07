def test_disabled_staff_permissions_when_logged_in(self):
        self.client.force_login(self.superuser)
        superuser = User.objects.get(username="super")
        superuser.is_staff = False
        superuser.save()

        response = self.client.get(self.index_url, follow=True)
        self.assertContains(response, 'id="login-form"')
        self.assertNotContains(response, "Log out")

        response = self.client.get(reverse("secure_view"), follow=True)
        self.assertContains(response, 'id="login-form"')
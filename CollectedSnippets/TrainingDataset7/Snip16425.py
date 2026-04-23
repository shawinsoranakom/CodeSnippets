def test_shortcut_view_only_available_to_staff(self):
        """
        Only admin users should be able to use the admin shortcut view.
        """
        model_ctype = ContentType.objects.get_for_model(ModelWithStringPrimaryKey)
        obj = ModelWithStringPrimaryKey.objects.create(string_pk="foo")
        shortcut_url = reverse("admin:view_on_site", args=(model_ctype.pk, obj.pk))

        # Not logged in: we should see the login page.
        response = self.client.get(shortcut_url, follow=True)
        self.assertTemplateUsed(response, "admin/login.html")

        # Logged in? Redirect.
        self.client.force_login(self.superuser)
        response = self.client.get(shortcut_url, follow=False)
        # Can't use self.assertRedirects() because User.get_absolute_url() is
        # silly.
        self.assertEqual(response.status_code, 302)
        # Domain may depend on contrib.sites tests also run
        self.assertRegex(response.url, "http://(testserver|example.com)/dummy/foo/")
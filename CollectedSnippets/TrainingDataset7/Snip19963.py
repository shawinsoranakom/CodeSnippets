def test_not_dependent_on_sites_app(self):
        """
        The view returns a complete URL regardless of whether the sites
        framework is installed.
        """
        user_ct = ContentType.objects.get_for_model(FooWithUrl)
        obj = FooWithUrl.objects.create(name="john")
        with self.modify_settings(INSTALLED_APPS={"append": "django.contrib.sites"}):
            response = shortcut(self.request, user_ct.id, obj.id)
            self.assertEqual(
                "http://%s/users/john/" % get_current_site(self.request).domain,
                response.headers.get("location"),
            )
        with self.modify_settings(INSTALLED_APPS={"remove": "django.contrib.sites"}):
            response = shortcut(self.request, user_ct.id, obj.id)
            self.assertEqual(
                "http://Example.com/users/john/", response.headers.get("location")
            )
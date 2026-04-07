def test_get_current_site(self):
        # The correct Site object is returned
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "80",
        }
        site = get_current_site(request)
        self.assertIsInstance(site, Site)
        self.assertEqual(site.id, settings.SITE_ID)

        # An exception is raised if the sites framework is installed
        # but there is no matching Site
        site.delete()
        with self.assertRaises(ObjectDoesNotExist):
            get_current_site(request)

        # A RequestSite is returned if the sites framework is not installed
        with self.modify_settings(INSTALLED_APPS={"remove": "django.contrib.sites"}):
            site = get_current_site(request)
            self.assertIsInstance(site, RequestSite)
            self.assertEqual(site.name, "example.com")
def test_get_current_site_no_site_id_and_handle_port_fallback(self):
        request = HttpRequest()
        s1 = self.site
        s2 = Site.objects.create(domain="example.com:80", name="example.com:80")

        # Host header without port
        request.META = {"HTTP_HOST": "example.com"}
        site = get_current_site(request)
        self.assertEqual(site, s1)

        # Host header with port - match, no fallback without port
        request.META = {"HTTP_HOST": "example.com:80"}
        site = get_current_site(request)
        self.assertEqual(site, s2)

        # Host header with port - no match, fallback without port
        request.META = {"HTTP_HOST": "example.com:81"}
        site = get_current_site(request)
        self.assertEqual(site, s1)

        # Host header with non-matching domain
        request.META = {"HTTP_HOST": "example.net"}
        with self.assertRaises(ObjectDoesNotExist):
            get_current_site(request)

        # Ensure domain for RequestSite always matches host header
        with self.modify_settings(INSTALLED_APPS={"remove": "django.contrib.sites"}):
            request.META = {"HTTP_HOST": "example.com"}
            site = get_current_site(request)
            self.assertEqual(site.name, "example.com")

            request.META = {"HTTP_HOST": "example.com:80"}
            site = get_current_site(request)
            self.assertEqual(site.name, "example.com:80")
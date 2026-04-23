def test_get_current_site_no_site_id(self):
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "80",
        }
        del settings.SITE_ID
        site = get_current_site(request)
        self.assertEqual(site.name, "example.com")
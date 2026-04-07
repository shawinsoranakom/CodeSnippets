def test_each_context_site_url_with_script_name(self):
        request = self.request_factory.get(
            reverse("test_adminsite:index"), SCRIPT_NAME="/my-script-name/"
        )
        request.user = self.u1
        self.assertEqual(site.each_context(request)["site_url"], "/my-script-name/")
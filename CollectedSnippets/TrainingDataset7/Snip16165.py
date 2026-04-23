def test_custom_admin_titles(self):
        request = self.request_factory.get(reverse("test_custom_adminsite:index"))
        request.user = self.u1
        ctx = custom_site.each_context(request)
        self.assertEqual(ctx["site_title"], "Custom title")
        self.assertEqual(ctx["site_header"], "Custom site")
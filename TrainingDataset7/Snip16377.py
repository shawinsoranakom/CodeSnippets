def test_js_minified_only_if_debug_is_false(self):
        """
        The minified versions of the JS files are only used when DEBUG is
        False.
        """
        with override_settings(DEBUG=False):
            response = self.client.get(reverse("admin:admin_views_section_add"))
            self.assertNotContains(response, "vendor/jquery/jquery.js")
            self.assertContains(response, "vendor/jquery/jquery.min.js")
            self.assertContains(response, "prepopulate.js")
            self.assertContains(response, "actions.js")
            self.assertContains(response, "inlines.js")
        with override_settings(DEBUG=True):
            response = self.client.get(reverse("admin:admin_views_section_add"))
            self.assertContains(response, "vendor/jquery/jquery.js")
            self.assertNotContains(response, "vendor/jquery/jquery.min.js")
            self.assertContains(response, "prepopulate.js")
            self.assertContains(response, "actions.js")
            self.assertContains(response, "inlines.js")
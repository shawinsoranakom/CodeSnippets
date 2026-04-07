def test_prepopulated_maxlength_localized(self):
        """
        Regression test for #15938: if USE_THOUSAND_SEPARATOR is set, make sure
        that maxLength (in the JavaScript) is rendered without separators.
        """
        response = self.client.get(
            reverse("admin:admin_views_prepopulatedpostlargeslug_add")
        )
        self.assertContains(response, "&quot;maxLength&quot;: 1000")
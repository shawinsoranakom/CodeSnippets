def test_view_only_add_form(self):
        """
        PrePopulatedPostReadOnlyAdmin.prepopulated_fields includes 'slug'
        which is present in the add view, even if the
        ModelAdmin.has_change_permission() returns False.
        """
        response = self.client.get(reverse("admin7:admin_views_prepopulatedpost_add"))
        self.assertContains(response, "data-prepopulated-fields=")
        self.assertContains(response, "&quot;id&quot;: &quot;#id_slug&quot;")
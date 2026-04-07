def test_view_only_change_form(self):
        """
        PrePopulatedPostReadOnlyAdmin.prepopulated_fields includes 'slug'. That
        doesn't break a view-only change view.
        """
        response = self.client.get(
            reverse("admin7:admin_views_prepopulatedpost_change", args=(self.p1.pk,))
        )
        self.assertContains(response, 'data-prepopulated-fields="[]"')
        self.assertContains(response, '<div class="readonly">%s</div>' % self.p1.slug)
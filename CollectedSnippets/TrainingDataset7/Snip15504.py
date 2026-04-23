def test_no_parent_callable_lookup(self):
        """
        Admin inline `readonly_field` shouldn't invoke parent ModelAdmin
        callable
        """
        # Identically named callable isn't present in the parent ModelAdmin,
        # rendering of the add view shouldn't explode
        response = self.client.get(reverse("admin:admin_inlines_novel_add"))
        # View should have the child inlines section
        self.assertContains(
            response,
            '<div class="js-inline-admin-formset inline-group" id="chapter_set-group"',
        )
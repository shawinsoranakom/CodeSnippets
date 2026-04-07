def test_help_text(self):
        """
        The inlines' model field help texts are displayed when using both the
        stacked and tabular layouts.
        """
        response = self.client.get(reverse("admin:admin_inlines_holder4_add"))
        self.assertContains(response, "Awesome stacked help text is awesome.", 4)
        self.assertContains(
            response,
            '<img src="/static/admin/img/icon-unknown.svg" '
            'class="help help-tooltip" width="10" height="10" '
            'alt="(Awesome tabular help text is awesome.)" '
            'title="Awesome tabular help text is awesome.">',
            1,
        )
        # ReadOnly fields
        response = self.client.get(reverse("admin:admin_inlines_capofamiglia_add"))
        self.assertContains(
            response,
            '<img src="/static/admin/img/icon-unknown.svg" '
            'class="help help-tooltip" width="10" height="10" '
            'alt="(Help text for ReadOnlyInline)" '
            'title="Help text for ReadOnlyInline">',
            1,
        )
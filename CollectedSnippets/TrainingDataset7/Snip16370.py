def test_filter_with_custom_template(self):
        """
        A custom template can be used to render an admin filter.
        """
        response = self.client.get(reverse("admin:admin_views_color2_changelist"))
        self.assertTemplateUsed(response, "custom_filter_template.html")
def test_field_prefix_css_classes(self):
        """
        Fields have a CSS class name with a 'field-' prefix.
        """
        response = self.client.get(reverse("admin:admin_views_post_add"))

        # The main form
        self.assertContains(response, 'class="form-row field-title"')
        self.assertContains(response, 'class="form-row field-content"')
        self.assertContains(response, 'class="form-row field-public"')
        self.assertContains(response, 'class="form-row field-awesomeness_level"')
        self.assertContains(response, 'class="form-row field-coolness"')
        self.assertContains(response, 'class="form-row field-value"')
        self.assertContains(response, 'class="form-row"')  # The lambda function

        # The tabular inline
        self.assertContains(response, '<td class="field-url">')
        self.assertContains(response, '<td class="field-posted">')
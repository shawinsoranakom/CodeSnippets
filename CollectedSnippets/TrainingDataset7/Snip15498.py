def test_tabular_inline_column_css_class(self):
        """
        Field names are included in the context to output a field-specific
        CSS class name in the column headers.
        """
        response = self.client.get(reverse("admin:admin_inlines_poll_add"))
        text_field, call_me_field = list(
            response.context["inline_admin_formset"].fields()
        )
        # Editable field.
        self.assertEqual(text_field["name"], "text")
        self.assertContains(response, '<th class="column-text required">')
        # Read-only field.
        self.assertEqual(call_me_field["name"], "call_me")
        self.assertContains(response, '<th class="column-call_me">')
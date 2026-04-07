def test_custom_form_tabular_inline_extra_field_label(self):
        response = self.client.get(reverse("admin:admin_inlines_outfititem_add"))
        _, extra_field = list(response.context["inline_admin_formset"].fields())
        self.assertEqual(extra_field["label"], "Extra field")
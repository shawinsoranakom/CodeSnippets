def test_custom_form_tabular_inline_overridden_label(self):
        """
        SomeChildModelForm.__init__() overrides the label of a form field.
        That label is displayed in the TabularInline.
        """
        response = self.client.get(reverse("admin:admin_inlines_someparentmodel_add"))
        field = list(response.context["inline_admin_formset"].fields())[0]
        self.assertEqual(field["label"], "new label")
        self.assertContains(
            response, '<th class="column-name required">New label</th>', html=True
        )
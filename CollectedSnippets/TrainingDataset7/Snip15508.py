def test_tabular_model_form_meta_readonly_field(self):
        """
        Tabular inlines use ModelForm.Meta.help_texts and labels for read-only
        fields.
        """
        response = self.client.get(reverse("admin:admin_inlines_someparentmodel_add"))
        self.assertContains(
            response,
            '<img src="/static/admin/img/icon-unknown.svg" '
            'class="help help-tooltip" width="10" height="10" '
            'alt="(Help text from ModelForm.Meta)" '
            'title="Help text from ModelForm.Meta">',
        )
        self.assertContains(response, "Label from ModelForm.Meta")
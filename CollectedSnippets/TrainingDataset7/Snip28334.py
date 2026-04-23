def test_replace_field_variant_2(self):
        # Should have the same result as before,
        # but 'fields' attribute specified differently
        class ReplaceField(forms.ModelForm):
            url = forms.BooleanField()

            class Meta:
                model = Category
                fields = ["url"]

        self.assertIsInstance(
            ReplaceField.base_fields["url"], forms.fields.BooleanField
        )
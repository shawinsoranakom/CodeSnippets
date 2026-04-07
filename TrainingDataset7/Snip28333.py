def test_replace_field(self):
        class ReplaceField(forms.ModelForm):
            url = forms.BooleanField()

            class Meta:
                model = Category
                fields = "__all__"

        self.assertIsInstance(
            ReplaceField.base_fields["url"], forms.fields.BooleanField
        )
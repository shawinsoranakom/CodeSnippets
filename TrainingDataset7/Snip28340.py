def test_exclude_nonexistent_field(self):
        class ExcludeFields(forms.ModelForm):
            class Meta:
                model = Category
                exclude = ["nonexistent"]

        self.assertEqual(list(ExcludeFields.base_fields), ["name", "slug", "url"])
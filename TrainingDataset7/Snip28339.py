def test_exclude_fields(self):
        class ExcludeFields(forms.ModelForm):
            class Meta:
                model = Category
                exclude = ["url"]

        self.assertEqual(list(ExcludeFields.base_fields), ["name", "slug"])
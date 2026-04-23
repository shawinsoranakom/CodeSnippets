def test_extra_fields(self):
        class ExtraFields(BaseCategoryForm):
            some_extra_field = forms.BooleanField()

        self.assertEqual(
            list(ExtraFields.base_fields), ["name", "slug", "url", "some_extra_field"]
        )
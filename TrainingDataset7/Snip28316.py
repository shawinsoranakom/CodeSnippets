def test_base_form(self):
        self.assertEqual(list(BaseCategoryForm.base_fields), ["name", "slug", "url"])
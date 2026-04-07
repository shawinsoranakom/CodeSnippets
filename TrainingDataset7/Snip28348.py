def test_subcategory_form(self):
        class SubCategoryForm(BaseCategoryForm):
            """Subclassing without specifying a Meta on the class will use
            the parent's Meta (or the first parent in the MRO if there are
            multiple parent classes).
            """

            pass

        self.assertEqual(list(SubCategoryForm.base_fields), ["name", "slug", "url"])
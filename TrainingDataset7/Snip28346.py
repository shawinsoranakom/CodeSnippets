def test_bad_form(self):
        # First class with a Meta class wins...
        class BadForm(ArticleForm, BaseCategoryForm):
            pass

        self.assertEqual(
            list(BadForm.base_fields),
            [
                "headline",
                "slug",
                "pub_date",
                "writer",
                "article",
                "categories",
                "status",
            ],
        )
def test_article_form(self):
        self.assertEqual(
            list(ArticleForm.base_fields),
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
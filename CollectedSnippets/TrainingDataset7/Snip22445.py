def test_foreign_key_raises_informative_does_not_exist(self):
        referrer = ArticleTranslation()
        with self.assertRaisesMessage(
            Article.DoesNotExist, "ArticleTranslation has no article"
        ):
            referrer.article
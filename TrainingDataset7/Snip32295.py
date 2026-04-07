def test_custom_named_field(self):
        article = CustomArticle.objects.create(
            title="Tantalizing News!",
            places_this_article_should_appear_id=settings.SITE_ID,
        )
        self.assertEqual(CustomArticle.on_site.get(), article)
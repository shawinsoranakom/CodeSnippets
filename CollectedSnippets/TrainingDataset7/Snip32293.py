def test_site_fk(self):
        article = ExclusiveArticle.objects.create(
            title="Breaking News!", site_id=settings.SITE_ID
        )
        self.assertEqual(ExclusiveArticle.on_site.get(), article)
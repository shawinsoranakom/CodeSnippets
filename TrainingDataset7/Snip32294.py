def test_sites_m2m(self):
        article = SyndicatedArticle.objects.create(title="Fresh News!")
        article.sites.add(Site.objects.get(id=settings.SITE_ID))
        article.sites.add(Site.objects.get(id=settings.SITE_ID + 1))
        article2 = SyndicatedArticle.objects.create(title="More News!")
        article2.sites.add(Site.objects.get(id=settings.SITE_ID + 1))
        self.assertEqual(SyndicatedArticle.on_site.get(), article)
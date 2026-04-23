def test_get_absolute_url_attributes(self):
        "A model can set attributes on the get_absolute_url method"
        self.assertTrue(
            getattr(UrlArticle.get_absolute_url, "purge", False),
            "The attributes of the original get_absolute_url must be added.",
        )
        article = UrlArticle.objects.get(pk=self.urlarticle.pk)
        self.assertTrue(
            getattr(article.get_absolute_url, "purge", False),
            "The attributes of the original get_absolute_url must be added.",
        )
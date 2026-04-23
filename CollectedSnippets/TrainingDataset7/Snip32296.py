def test_invalid_name(self):
        class InvalidArticle(models.Model):
            on_site = CurrentSiteManager("places_this_article_should_appear")

        errors = InvalidArticle.check()
        expected = [
            checks.Error(
                "CurrentSiteManager could not find a field named "
                "'places_this_article_should_appear'.",
                obj=InvalidArticle.on_site,
                id="sites.E001",
            )
        ]
        self.assertEqual(errors, expected)
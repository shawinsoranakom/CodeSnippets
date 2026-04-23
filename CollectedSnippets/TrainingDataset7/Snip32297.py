def test_invalid_field_type(self):
        class ConfusedArticle(models.Model):
            site = models.IntegerField()
            on_site = CurrentSiteManager()

        errors = ConfusedArticle.check()
        expected = [
            checks.Error(
                "CurrentSiteManager cannot use 'ConfusedArticle.site' as it is "
                "not a foreign key or a many-to-many field.",
                obj=ConfusedArticle.on_site,
                id="sites.E002",
            )
        ]
        self.assertEqual(errors, expected)
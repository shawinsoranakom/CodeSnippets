def test_m2m_tables_in_subpackage_models(self):
        """
        Regression for #12168: models split into subpackages still get M2M
        tables.
        """
        p = Publication.objects.create(title="FooBar")

        site = Site.objects.create(name="example.com")

        a = Article.objects.create(headline="a foo headline")
        a.publications.add(p)
        a.sites.add(site)

        a = Article.objects.get(id=a.pk)
        self.assertEqual(a.id, a.pk)
        self.assertEqual(a.sites.count(), 1)
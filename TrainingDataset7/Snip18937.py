def test_lookup_by_primary_key(self):
        # Lookup by a primary key is the most common case, so Django
        # provides a shortcut for primary-key exact lookups.
        # The following is identical to articles.get(id=a.id).
        self.assertEqual(Article.objects.get(pk=self.a.id), self.a)

        # pk can be used as a shortcut for the primary key name in any query.
        self.assertSequenceEqual(Article.objects.filter(pk__in=[self.a.id]), [self.a])

        # Model instances of the same type and same ID are considered equal.
        a = Article.objects.get(pk=self.a.id)
        b = Article.objects.get(pk=self.a.id)
        self.assertEqual(a, b)
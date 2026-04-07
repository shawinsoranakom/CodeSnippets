def test_prefetched_cache_cleared(self):
        a = Article.objects.create(pub_date=datetime(2005, 7, 28))
        s = SelfRef.objects.create(article=a, article_cited=a)
        # refresh_from_db() without fields=[...]
        a1_prefetched = Article.objects.prefetch_related("selfref_set", "cited").first()
        self.assertCountEqual(a1_prefetched.selfref_set.all(), [s])
        self.assertCountEqual(a1_prefetched.cited.all(), [s])
        s.article = None
        s.article_cited = None
        s.save()
        # Relation is cleared and prefetch cache is stale.
        self.assertCountEqual(a1_prefetched.selfref_set.all(), [s])
        self.assertCountEqual(a1_prefetched.cited.all(), [s])
        a1_prefetched.refresh_from_db()
        # Cache was cleared and new results are available.
        self.assertCountEqual(a1_prefetched.selfref_set.all(), [])
        self.assertCountEqual(a1_prefetched.cited.all(), [])
        # refresh_from_db() with fields=[...]
        a2_prefetched = Article.objects.prefetch_related("selfref_set", "cited").first()
        self.assertCountEqual(a2_prefetched.selfref_set.all(), [])
        self.assertCountEqual(a2_prefetched.cited.all(), [])
        s.article = a
        s.article_cited = a
        s.save()
        # Relation is added and prefetch cache is stale.
        self.assertCountEqual(a2_prefetched.selfref_set.all(), [])
        self.assertCountEqual(a2_prefetched.cited.all(), [])
        fields = ["selfref_set", "cited"]
        a2_prefetched.refresh_from_db(fields=fields)
        self.assertEqual(fields, ["selfref_set", "cited"])
        # Cache was cleared and new results are available.
        self.assertCountEqual(a2_prefetched.selfref_set.all(), [s])
        self.assertCountEqual(a2_prefetched.cited.all(), [s])
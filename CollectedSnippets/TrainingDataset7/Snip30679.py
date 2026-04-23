def test_queryset_reuse(self):
        # Using querysets doesn't mutate aliases.
        authors = Author.objects.filter(Q(name="a1") | Q(name="nonexistent"))
        self.assertEqual(Ranking.objects.filter(author__in=authors).get(), self.rank3)
        self.assertEqual(authors.count(), 1)
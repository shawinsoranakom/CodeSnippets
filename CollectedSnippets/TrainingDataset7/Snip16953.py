def test_fkey_aggregate(self):
        explicit = list(Author.objects.annotate(Count("book__id")))
        implicit = list(Author.objects.annotate(Count("book")))
        self.assertCountEqual(explicit, implicit)
def test_clear(self):
        with self.assertNumQueries(5):
            with_prefetch = Author.objects.prefetch_related("books")
            without_prefetch = with_prefetch.prefetch_related(None)
            [list(a.books.all()) for a in without_prefetch]
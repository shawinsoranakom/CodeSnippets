def test_defer(self):
        # One query for the list and one query for the deferred title.
        with self.assertNumQueries(2):
            self.assertQuerySetEqual(
                Author.objects.annotate(
                    book_alice=FilteredRelation(
                        "book", condition=Q(book__title__iexact="poem by alice")
                    ),
                )
                .filter(book_alice__isnull=False)
                .select_related("book_alice")
                .defer("book_alice__title"),
                ["Poem by Alice"],
                lambda author: author.book_alice.title,
            )
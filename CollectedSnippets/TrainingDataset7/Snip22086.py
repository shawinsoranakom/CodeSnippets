def test_values(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            )
            .filter(book_alice__isnull=False)
            .values(),
            [
                {
                    "id": self.author1.pk,
                    "name": "Alice",
                    "content_type_id": None,
                    "object_id": None,
                }
            ],
        )
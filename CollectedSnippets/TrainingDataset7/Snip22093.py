def test_only_not_supported(self):
        msg = "only() is not supported with FilteredRelation."
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            ).filter(book_alice__isnull=False).select_related("book_alice").only(
                "book_alice__state"
            )
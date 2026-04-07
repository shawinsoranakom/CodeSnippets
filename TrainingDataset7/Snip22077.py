def test_period_forbidden(self):
        msg = (
            "FilteredRelation doesn't support aliases with periods (got 'book.alice')."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                **{
                    "book.alice": FilteredRelation(
                        "book", condition=Q(book__title__iexact="poem by alice")
                    )
                }
            )
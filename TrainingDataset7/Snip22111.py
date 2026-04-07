def test_with_prefetch_related(self):
        msg = "prefetch_related() is not supported with FilteredRelation."
        qs = Author.objects.annotate(
            book_title_contains_b=FilteredRelation(
                "book", condition=Q(book__title__icontains="b")
            ),
        ).filter(
            book_title_contains_b__isnull=False,
        )
        with self.assertRaisesMessage(ValueError, msg):
            qs.prefetch_related("book_title_contains_b")
        with self.assertRaisesMessage(ValueError, msg):
            qs.prefetch_related("book_title_contains_b__editor")
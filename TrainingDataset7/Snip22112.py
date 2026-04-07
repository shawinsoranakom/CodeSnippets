def test_with_generic_foreign_key(self):
        self.assertSequenceEqual(
            Book.objects.annotate(
                generic_authored_book=FilteredRelation(
                    "generic_author", condition=Q(generic_author__isnull=False)
                ),
            ).filter(generic_authored_book__isnull=False),
            [self.book1],
        )
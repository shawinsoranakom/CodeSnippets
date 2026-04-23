def test_with_m2m_multijoin(self):
        qs = (
            Author.objects.annotate(
                favorite_books_written_by_jane=FilteredRelation(
                    "favorite_books",
                    condition=Q(favorite_books__author=self.author2),
                )
            )
            .filter(favorite_books_written_by_jane__editor__name="b")
            .distinct()
        )
        self.assertSequenceEqual(qs, [self.author1])
def test_select_related_foreign_key(self):
        qs = (
            Book.objects.annotate(
                author_join=FilteredRelation("author"),
            )
            .select_related("author_join")
            .order_by("pk")
        )
        with self.assertNumQueries(1):
            self.assertQuerySetEqual(
                qs,
                [
                    (self.book1, self.author1),
                    (self.book2, self.author2),
                    (self.book3, self.author2),
                    (self.book4, self.author1),
                ],
                lambda x: (x, x.author_join),
            )
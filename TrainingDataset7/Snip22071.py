def test_select_related_foreign_key_for_update_of(self):
        with transaction.atomic():
            qs = (
                Book.objects.annotate(
                    author_join=FilteredRelation("author"),
                )
                .select_related("author_join")
                .select_for_update(of=("self",))
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
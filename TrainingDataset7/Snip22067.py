def test_select_related(self):
        qs = (
            Author.objects.annotate(
                book_join=FilteredRelation("book"),
            )
            .select_related("book_join__editor")
            .order_by("pk", "book_join__pk")
        )
        with self.assertNumQueries(1):
            self.assertQuerySetEqual(
                qs,
                [
                    (self.author1, self.book1, self.editor_a, self.author1),
                    (self.author1, self.book4, self.editor_a, self.author1),
                    (self.author2, self.book2, self.editor_b, self.author2),
                    (self.author2, self.book3, self.editor_b, self.author2),
                ],
                lambda x: (x, x.book_join, x.book_join.editor, x.book_join.author),
            )
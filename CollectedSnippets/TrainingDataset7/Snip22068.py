def test_select_related_multiple(self):
        qs = (
            Book.objects.annotate(
                author_join=FilteredRelation("author"),
                editor_join=FilteredRelation("editor"),
            )
            .select_related("author_join", "editor_join")
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            qs,
            [
                (self.book1, self.author1, self.editor_a),
                (self.book2, self.author2, self.editor_b),
                (self.book3, self.author2, self.editor_b),
                (self.book4, self.author1, self.editor_a),
            ],
            lambda x: (x, x.author_join, x.editor_join),
        )
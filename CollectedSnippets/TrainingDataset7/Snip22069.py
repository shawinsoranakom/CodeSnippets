def test_select_related_with_empty_relation(self):
        qs = (
            Author.objects.annotate(
                book_join=FilteredRelation("book", condition=Q(pk=-1)),
            )
            .select_related("book_join")
            .order_by("pk")
        )
        self.assertSequenceEqual(qs, [self.author1, self.author2])
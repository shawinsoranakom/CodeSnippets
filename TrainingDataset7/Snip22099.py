def test_nested_chained_relations(self):
        qs = (
            Author.objects.annotate(
                my_books=FilteredRelation(
                    "book",
                    condition=Q(book__title__icontains="book by"),
                ),
                preferred_by_authors=FilteredRelation(
                    "my_books__preferred_by_authors",
                    condition=Q(my_books__preferred_by_authors__name="Alice"),
                ),
            )
            .annotate(
                author=F("name"),
                book_title=F("my_books__title"),
                preferred_by_author_pk=F("preferred_by_authors"),
            )
            .order_by("author", "book_title", "preferred_by_author_pk")
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Alice", "The book by Alice", None),
                ("Jane", "The book by Jane A", self.author1.pk),
                ("Jane", "The book by Jane B", self.author1.pk),
            ],
            lambda x: (x.author, x.book_title, x.preferred_by_author_pk),
        )
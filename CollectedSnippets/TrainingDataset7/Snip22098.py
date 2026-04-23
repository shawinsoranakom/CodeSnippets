def test_nested_m2m_filtered(self):
        qs = (
            Book.objects.annotate(
                favorite_book=FilteredRelation(
                    "author__favorite_books",
                    condition=Q(author__favorite_books__title__icontains="book by"),
                ),
            )
            .values(
                "title",
                "favorite_book__pk",
            )
            .order_by("title", "favorite_book__title")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"title": self.book1.title, "favorite_book__pk": self.book2.pk},
                {"title": self.book1.title, "favorite_book__pk": self.book3.pk},
                {"title": self.book4.title, "favorite_book__pk": self.book2.pk},
                {"title": self.book4.title, "favorite_book__pk": self.book3.pk},
                {"title": self.book2.title, "favorite_book__pk": None},
                {"title": self.book3.title, "favorite_book__pk": None},
            ],
        )
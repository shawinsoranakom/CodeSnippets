def test_order_by_fk_attname(self):
        """
        ordering by a foreign key by its attribute name prevents the query
        from inheriting its related model ordering option (#19195).
        """
        authors = list(Author.objects.order_by("id"))
        for i in range(1, 5):
            author = authors[i - 1]
            article = getattr(self, "a%d" % (5 - i))
            article.author = author
            article.save(update_fields={"author"})

        self.assertQuerySetEqual(
            Article.objects.order_by("author_id"),
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )
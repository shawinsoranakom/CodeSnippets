def test_add(self):
        # Create an Article via the Reporter object.
        new_article = self.r.article_set.create(
            headline="John's second story", pub_date=datetime.date(2005, 7, 29)
        )
        self.assertEqual(repr(new_article), "<Article: John's second story>")
        self.assertEqual(new_article.reporter.id, self.r.id)

        # Create a new article, and add it to the article set.
        new_article2 = Article(
            headline="Paul's story", pub_date=datetime.date(2006, 1, 17)
        )
        msg = (
            "<Article: Paul's story> instance isn't saved. Use bulk=False or save the "
            "object first."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.r.article_set.add(new_article2)

        self.r.article_set.add(new_article2, bulk=False)
        self.assertEqual(new_article2.reporter.id, self.r.id)
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [new_article, new_article2, self.a],
        )

        # Add the same article to a different article set - check that it
        # moves.
        self.r2.article_set.add(new_article2)
        self.assertEqual(new_article2.reporter.id, self.r2.id)
        self.assertSequenceEqual(self.r2.article_set.all(), [new_article2])

        # Adding an object of the wrong type raises TypeError.
        with transaction.atomic():
            with self.assertRaisesMessage(
                TypeError, "'Article' instance expected, got <Reporter:"
            ):
                self.r.article_set.add(self.r2)
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [new_article, self.a],
        )
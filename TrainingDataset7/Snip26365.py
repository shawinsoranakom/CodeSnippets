def test_set(self):
        new_article = self.r.article_set.create(
            headline="John's second story", pub_date=datetime.date(2005, 7, 29)
        )
        new_article2 = self.r2.article_set.create(
            headline="Paul's story", pub_date=datetime.date(2006, 1, 17)
        )

        # Assign the article to the reporter.
        new_article2.reporter = self.r
        new_article2.save()
        self.assertEqual(repr(new_article2.reporter), "<Reporter: John Smith>")
        self.assertEqual(new_article2.reporter.id, self.r.id)
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [new_article, new_article2, self.a],
        )
        self.assertSequenceEqual(self.r2.article_set.all(), [])

        # Set the article back again.
        self.r2.article_set.set([new_article, new_article2])
        self.assertSequenceEqual(self.r.article_set.all(), [self.a])
        self.assertSequenceEqual(
            self.r2.article_set.all(),
            [new_article, new_article2],
        )

        # Funny case - because the ForeignKey cannot be null,
        # existing members of the set must remain.
        self.r.article_set.set([new_article])
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [new_article, self.a],
        )
        self.assertSequenceEqual(self.r2.article_set.all(), [new_article2])
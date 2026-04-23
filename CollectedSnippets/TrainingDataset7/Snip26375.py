def test_delete(self):
        new_article1 = self.r.article_set.create(
            headline="John's second story",
            pub_date=datetime.date(2005, 7, 29),
        )
        new_article2 = self.r2.article_set.create(
            headline="Paul's story",
            pub_date=datetime.date(2006, 1, 17),
        )
        new_article3 = Article.objects.create(
            headline="Third article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=self.r.id,
        )
        new_article4 = Article.objects.create(
            headline="Fourth article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=str(self.r.id),
        )
        # If you delete a reporter, their articles will be deleted.
        self.assertSequenceEqual(
            Article.objects.all(),
            [new_article4, new_article1, new_article2, new_article3, self.a],
        )
        self.assertSequenceEqual(
            Reporter.objects.order_by("first_name"),
            [self.r, self.r2],
        )
        self.r2.delete()
        self.assertSequenceEqual(
            Article.objects.all(),
            [new_article4, new_article1, new_article3, self.a],
        )
        self.assertSequenceEqual(Reporter.objects.order_by("first_name"), [self.r])
        # You can delete using a JOIN in the query.
        Reporter.objects.filter(article__headline__startswith="This").delete()
        self.assertSequenceEqual(Reporter.objects.all(), [])
        self.assertSequenceEqual(Article.objects.all(), [])
def test_selects(self):
        new_article1 = self.r.article_set.create(
            headline="John's second story",
            pub_date=datetime.date(2005, 7, 29),
        )
        new_article2 = self.r2.article_set.create(
            headline="Paul's story",
            pub_date=datetime.date(2006, 1, 17),
        )
        # Reporter objects have access to their related Article objects.
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [new_article1, self.a],
        )
        self.assertSequenceEqual(
            self.r.article_set.filter(headline__startswith="This"), [self.a]
        )
        self.assertEqual(self.r.article_set.count(), 2)
        self.assertEqual(self.r2.article_set.count(), 1)
        # Get articles by id
        self.assertSequenceEqual(Article.objects.filter(id__exact=self.a.id), [self.a])
        self.assertSequenceEqual(Article.objects.filter(pk=self.a.id), [self.a])
        # Query on an article property
        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="This"), [self.a]
        )
        # The API automatically follows relationships as far as you need.
        # Use double underscores to separate relationships.
        # This works as many levels deep as you want. There's no limit.
        # Find all Articles for any Reporter whose first name is "John".
        self.assertSequenceEqual(
            Article.objects.filter(reporter__first_name__exact="John"),
            [new_article1, self.a],
        )
        # Implied __exact also works
        self.assertSequenceEqual(
            Article.objects.filter(reporter__first_name="John"),
            [new_article1, self.a],
        )
        # Query twice over the related field.
        self.assertSequenceEqual(
            Article.objects.filter(
                reporter__first_name__exact="John", reporter__last_name__exact="Smith"
            ),
            [new_article1, self.a],
        )
        # Find all Articles for a Reporter.
        # Use direct ID check, pk check, and object comparison
        self.assertSequenceEqual(
            Article.objects.filter(reporter__id__exact=self.r.id),
            [new_article1, self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(reporter__pk=self.r.id),
            [new_article1, self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(reporter=self.r.id),
            [new_article1, self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(reporter=self.r),
            [new_article1, self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(reporter__in=[self.r.id, self.r2.id]).distinct(),
            [new_article1, new_article2, self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(reporter__in=[self.r, self.r2]).distinct(),
            [new_article1, new_article2, self.a],
        )
        # You can also use a queryset instead of a literal list of instances.
        # The queryset must be reduced to a list of values using values(),
        # then converted into a query
        self.assertSequenceEqual(
            Article.objects.filter(
                reporter__in=Reporter.objects.filter(first_name="John")
                .values("pk")
                .query
            ).distinct(),
            [new_article1, self.a],
        )
def test_reverse_selects(self):
        a3 = Article.objects.create(
            headline="Third article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=self.r.id,
        )
        Article.objects.create(
            headline="Fourth article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=self.r.id,
        )
        john_smith = [self.r]
        # Reporters can be queried
        self.assertSequenceEqual(
            Reporter.objects.filter(id__exact=self.r.id), john_smith
        )
        self.assertSequenceEqual(Reporter.objects.filter(pk=self.r.id), john_smith)
        self.assertSequenceEqual(
            Reporter.objects.filter(first_name__startswith="John"), john_smith
        )
        # Reporters can query in opposite direction of ForeignKey definition
        self.assertSequenceEqual(
            Reporter.objects.filter(article__id__exact=self.a.id), john_smith
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(article__pk=self.a.id), john_smith
        )
        self.assertSequenceEqual(Reporter.objects.filter(article=self.a.id), john_smith)
        self.assertSequenceEqual(Reporter.objects.filter(article=self.a), john_smith)
        self.assertSequenceEqual(
            Reporter.objects.filter(article__in=[self.a.id, a3.id]).distinct(),
            john_smith,
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(article__in=[self.a.id, a3]).distinct(), john_smith
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(article__in=[self.a, a3]).distinct(), john_smith
        )
        self.assertCountEqual(
            Reporter.objects.filter(article__headline__startswith="T"),
            [self.r, self.r],
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(article__headline__startswith="T").distinct(),
            john_smith,
        )

        # Counting in the opposite direction works in conjunction with
        # distinct()
        self.assertEqual(
            Reporter.objects.filter(article__headline__startswith="T").count(), 2
        )
        self.assertEqual(
            Reporter.objects.filter(article__headline__startswith="T")
            .distinct()
            .count(),
            1,
        )

        # Queries can go round in circles.
        self.assertCountEqual(
            Reporter.objects.filter(article__reporter__first_name__startswith="John"),
            [self.r, self.r, self.r],
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(
                article__reporter__first_name__startswith="John"
            ).distinct(),
            john_smith,
        )
        self.assertSequenceEqual(
            Reporter.objects.filter(article__reporter__exact=self.r).distinct(),
            john_smith,
        )

        # Implied __exact also works.
        self.assertSequenceEqual(
            Reporter.objects.filter(article__reporter=self.r).distinct(), john_smith
        )

        # It's possible to use values() calls across many-to-one relations.
        # (Note, too, that we clear the ordering here so as not to drag the
        # 'headline' field into the columns being used to determine uniqueness)
        d = {"reporter__first_name": "John", "reporter__last_name": "Smith"}
        qs = (
            Article.objects.filter(
                reporter=self.r,
            )
            .distinct()
            .order_by()
            .values("reporter__first_name", "reporter__last_name")
        )
        self.assertEqual([d], list(qs))
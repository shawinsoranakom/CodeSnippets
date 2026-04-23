def test_selects(self):
        # We can perform kwarg queries across m2m relationships
        self.assertSequenceEqual(
            Article.objects.filter(publications__id__exact=self.p1.id),
            [self.a1, self.a2],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications__pk=self.p1.id),
            [self.a1, self.a2],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications=self.p1.id),
            [self.a1, self.a2],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications=self.p1),
            [self.a1, self.a2],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications__title__startswith="Science"),
            [self.a3, self.a2, self.a2, self.a4],
        )
        self.assertSequenceEqual(
            Article.objects.filter(
                publications__title__startswith="Science"
            ).distinct(),
            [self.a3, self.a2, self.a4],
        )

        # The count() function respects distinct() as well.
        self.assertEqual(
            Article.objects.filter(publications__title__startswith="Science").count(), 4
        )
        self.assertEqual(
            Article.objects.filter(publications__title__startswith="Science")
            .distinct()
            .count(),
            3,
        )
        self.assertSequenceEqual(
            Article.objects.filter(
                publications__in=[self.p1.id, self.p2.id]
            ).distinct(),
            [self.a1, self.a3, self.a2, self.a4],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications__in=[self.p1.id, self.p2]).distinct(),
            [self.a1, self.a3, self.a2, self.a4],
        )
        self.assertSequenceEqual(
            Article.objects.filter(publications__in=[self.p1, self.p2]).distinct(),
            [self.a1, self.a3, self.a2, self.a4],
        )

        # Excluding a related item works as you would expect, too (although the
        # SQL involved is a little complex).
        self.assertSequenceEqual(
            Article.objects.exclude(publications=self.p2),
            [self.a1],
        )
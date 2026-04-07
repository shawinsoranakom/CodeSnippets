def test_explicit_fk(self):
        # Create a new Article with get_or_create using an explicit value
        # for a ForeignKey.
        a2, created = Article.objects.get_or_create(
            headline="John's second test",
            pub_date=datetime.date(2011, 5, 7),
            reporter_id=self.r.id,
        )
        self.assertTrue(created)
        self.assertEqual(a2.reporter.id, self.r.id)

        # You can specify filters containing the explicit FK value.
        self.assertSequenceEqual(
            Article.objects.filter(reporter_id__exact=self.r.id),
            [a2, self.a],
        )

        # Create an Article by Paul for the same date.
        a3 = Article.objects.create(
            headline="Paul's commentary",
            pub_date=datetime.date(2011, 5, 7),
            reporter_id=self.r2.id,
        )
        self.assertEqual(a3.reporter.id, self.r2.id)

        # Get should respect explicit foreign keys as well.
        msg = "get() returned more than one Article -- it returned 2!"
        with self.assertRaisesMessage(MultipleObjectsReturned, msg):
            Article.objects.get(reporter_id=self.r.id)
        self.assertEqual(
            repr(a3),
            repr(
                Article.objects.get(
                    reporter_id=self.r2.id, pub_date=datetime.date(2011, 5, 7)
                )
            ),
        )
def test_latest(self):
        # Because no Articles exist yet, latest() raises ArticleDoesNotExist.
        with self.assertRaises(Article.DoesNotExist):
            Article.objects.latest()

        a1 = Article.objects.create(
            headline="Article 1",
            pub_date=datetime(2005, 7, 26),
            expire_date=datetime(2005, 9, 1),
        )
        a2 = Article.objects.create(
            headline="Article 2",
            pub_date=datetime(2005, 7, 27),
            expire_date=datetime(2005, 7, 28),
        )
        a3 = Article.objects.create(
            headline="Article 3",
            pub_date=datetime(2005, 7, 27),
            expire_date=datetime(2005, 8, 27),
        )
        a4 = Article.objects.create(
            headline="Article 4",
            pub_date=datetime(2005, 7, 28),
            expire_date=datetime(2005, 7, 30),
        )

        # Get the latest Article.
        self.assertEqual(Article.objects.latest(), a4)
        # Get the latest Article that matches certain filters.
        self.assertEqual(
            Article.objects.filter(pub_date__lt=datetime(2005, 7, 27)).latest(), a1
        )

        # Pass a custom field name to latest() to change the field that's used
        # to determine the latest object.
        self.assertEqual(Article.objects.latest("expire_date"), a1)
        self.assertEqual(
            Article.objects.filter(pub_date__gt=datetime(2005, 7, 26)).latest(
                "expire_date"
            ),
            a3,
        )

        # latest() overrides any other ordering specified on the query
        # (#11283).
        self.assertEqual(Article.objects.order_by("id").latest(), a4)

        # Error is raised if get_latest_by isn't in Model.Meta.
        Article.objects.model._meta.get_latest_by = None
        with self.assertRaisesMessage(
            ValueError,
            "earliest() and latest() require either fields as positional "
            "arguments or 'get_latest_by' in the model's Meta.",
        ):
            Article.objects.latest()

        # Latest publication date, latest expire date.
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 27)).latest(
                "pub_date", "expire_date"
            ),
            a3,
        )
        # Latest publication date, earliest expire date.
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 27)).latest(
                "pub_date", "-expire_date"
            ),
            a2,
        )

        # Meta.get_latest_by may be a tuple.
        Article.objects.model._meta.get_latest_by = ("pub_date", "expire_date")
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 27)).latest(), a3
        )
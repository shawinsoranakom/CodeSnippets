def test_earliest(self):
        # Because no Articles exist yet, earliest() raises ArticleDoesNotExist.
        with self.assertRaises(Article.DoesNotExist):
            Article.objects.earliest()

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
            pub_date=datetime(2005, 7, 28),
            expire_date=datetime(2005, 8, 27),
        )
        a4 = Article.objects.create(
            headline="Article 4",
            pub_date=datetime(2005, 7, 28),
            expire_date=datetime(2005, 7, 30),
        )

        # Get the earliest Article.
        self.assertEqual(Article.objects.earliest(), a1)
        # Get the earliest Article that matches certain filters.
        self.assertEqual(
            Article.objects.filter(pub_date__gt=datetime(2005, 7, 26)).earliest(), a2
        )

        # Pass a custom field name to earliest() to change the field that's
        # used to determine the earliest object.
        self.assertEqual(Article.objects.earliest("expire_date"), a2)
        self.assertEqual(
            Article.objects.filter(pub_date__gt=datetime(2005, 7, 26)).earliest(
                "expire_date"
            ),
            a2,
        )

        # earliest() overrides any other ordering specified on the query.
        # Refs #11283.
        self.assertEqual(Article.objects.order_by("id").earliest(), a1)

        # Error is raised if the user forgot to add a get_latest_by
        # in the Model.Meta
        Article.objects.model._meta.get_latest_by = None
        with self.assertRaisesMessage(
            ValueError,
            "earliest() and latest() require either fields as positional "
            "arguments or 'get_latest_by' in the model's Meta.",
        ):
            Article.objects.earliest()

        # Earliest publication date, earliest expire date.
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 28)).earliest(
                "pub_date", "expire_date"
            ),
            a4,
        )
        # Earliest publication date, latest expire date.
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 28)).earliest(
                "pub_date", "-expire_date"
            ),
            a3,
        )

        # Meta.get_latest_by may be a tuple.
        Article.objects.model._meta.get_latest_by = ("pub_date", "expire_date")
        self.assertEqual(
            Article.objects.filter(pub_date=datetime(2005, 7, 28)).earliest(), a4
        )
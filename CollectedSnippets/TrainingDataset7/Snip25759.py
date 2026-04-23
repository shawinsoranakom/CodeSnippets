def setUpTestData(cls):
        # Create a few Authors.
        cls.au1 = Author.objects.create(name="Author 1", alias="a1", bio="x" * 4001)
        cls.au2 = Author.objects.create(name="Author 2", alias="a2")
        # Create a few Articles.
        cls.a1 = Article.objects.create(
            headline="Article 1",
            pub_date=datetime(2005, 7, 26),
            author=cls.au1,
            slug="a1",
        )
        cls.a2 = Article.objects.create(
            headline="Article 2",
            pub_date=datetime(2005, 7, 27),
            author=cls.au1,
            slug="a2",
        )
        cls.a3 = Article.objects.create(
            headline="Article 3",
            pub_date=datetime(2005, 7, 27),
            author=cls.au1,
            slug="a3",
        )
        cls.a4 = Article.objects.create(
            headline="Article 4",
            pub_date=datetime(2005, 7, 28),
            author=cls.au1,
            slug="a4",
        )
        cls.a5 = Article.objects.create(
            headline="Article 5",
            pub_date=datetime(2005, 8, 1, 9, 0),
            author=cls.au2,
            slug="a5",
        )
        cls.a6 = Article.objects.create(
            headline="Article 6",
            pub_date=datetime(2005, 8, 1, 8, 0),
            author=cls.au2,
            slug="a6",
        )
        cls.a7 = Article.objects.create(
            headline="Article 7",
            pub_date=datetime(2005, 7, 27),
            author=cls.au2,
            slug="a7",
        )
        # Create a few Tags.
        cls.t1 = Tag.objects.create(name="Tag 1")
        cls.t1.articles.add(cls.a1, cls.a2, cls.a3)
        cls.t2 = Tag.objects.create(name="Tag 2")
        cls.t2.articles.add(cls.a3, cls.a4, cls.a5)
        cls.t3 = Tag.objects.create(name="Tag 3")
        cls.t3.articles.add(cls.a5, cls.a6, cls.a7)
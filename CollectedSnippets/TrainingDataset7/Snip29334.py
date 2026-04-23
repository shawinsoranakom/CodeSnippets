def setUpTestData(cls):
        cls.a1 = Article.objects.create(
            headline="Article 1", pub_date=datetime(2005, 7, 26)
        )
        cls.a2 = Article.objects.create(
            headline="Article 2", pub_date=datetime(2005, 7, 27)
        )
        cls.a3 = Article.objects.create(
            headline="Article 3", pub_date=datetime(2005, 7, 27)
        )
        cls.a4 = Article.objects.create(
            headline="Article 4", pub_date=datetime(2005, 7, 28)
        )
        cls.author_1 = Author.objects.create(name="Name 1")
        cls.author_2 = Author.objects.create(name="Name 2")
        for i in range(2):
            Author.objects.create()
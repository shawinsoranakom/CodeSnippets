def setUpTestData(cls):
        cls.a1 = Article.objects.create(
            headline="Hello", pub_date=datetime(2005, 11, 27)
        ).pk
        cls.a2 = Article.objects.create(
            headline="Goodbye", pub_date=datetime(2005, 11, 28)
        ).pk
        cls.a3 = Article.objects.create(
            headline="Hello and goodbye", pub_date=datetime(2005, 11, 29)
        ).pk
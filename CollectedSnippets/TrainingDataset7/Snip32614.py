def setUpTestData(cls):
        cls.e1 = Entry.objects.create(
            title="My first entry",
            updated=datetime.datetime(1980, 1, 1, 12, 30),
            published=datetime.datetime(1986, 9, 25, 20, 15, 00),
        )
        cls.e2 = Entry.objects.create(
            title="My second entry",
            updated=datetime.datetime(2008, 1, 2, 12, 30),
            published=datetime.datetime(2006, 3, 17, 18, 0),
        )
        cls.e3 = Entry.objects.create(
            title="My third entry",
            updated=datetime.datetime(2008, 1, 2, 13, 30),
            published=datetime.datetime(2005, 6, 14, 10, 45),
        )
        cls.e4 = Entry.objects.create(
            title="A & B < C > D",
            updated=datetime.datetime(2008, 1, 3, 13, 30),
            published=datetime.datetime(2005, 11, 25, 12, 11, 23),
        )
        cls.e5 = Entry.objects.create(
            title="My last entry",
            updated=datetime.datetime(2013, 1, 20, 0, 0),
            published=datetime.datetime(2013, 3, 25, 20, 0),
        )
        cls.a1 = Article.objects.create(
            title="My first article",
            entry=cls.e1,
            updated=datetime.datetime(1986, 11, 21, 9, 12, 18),
            published=datetime.datetime(1986, 10, 21, 9, 12, 18),
        )
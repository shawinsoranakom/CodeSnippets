def setUpTestData(cls):
        cls.a1 = Author.objects.create(name="test", age=40)
        cls.a2 = Author.objects.create(name="test2", age=60)
        cls.a3 = Author.objects.create(name="test3", age=100)
        cls.p1 = Publisher.objects.create(
            name="Apress", num_awards=3, duration=datetime.timedelta(days=1)
        )
        cls.b1 = Book.objects.create(
            isbn="159059725",
            name="The Definitive Guide to Django: Web Development Done Right",
            pages=447,
            rating=4.5,
            price=Decimal("30.00"),
            contact=cls.a1,
            publisher=cls.p1,
            pubdate=datetime.date(2007, 12, 6),
        )
        cls.b2 = Book.objects.create(
            isbn="067232959",
            name="Sams Teach Yourself Django in 24 Hours",
            pages=528,
            rating=3.0,
            price=Decimal("23.09"),
            contact=cls.a2,
            publisher=cls.p1,
            pubdate=datetime.date(2008, 3, 3),
        )
        cls.b3 = Book.objects.create(
            isbn="159059996",
            name="Practical Django Projects",
            pages=600,
            rating=4.5,
            price=Decimal("29.69"),
            contact=cls.a3,
            publisher=cls.p1,
            pubdate=datetime.date(2008, 6, 23),
        )
        cls.a1.friends.add(cls.a2)
        cls.a1.friends.add(cls.a3)
        cls.b1.authors.add(cls.a1)
        cls.b1.authors.add(cls.a3)
        cls.b2.authors.add(cls.a2)
        cls.b3.authors.add(cls.a3)
def setUpTestData(cls):
        cls.a1 = Author.objects.create(age=1)
        cls.a2 = Author.objects.create(age=2)
        cls.p1 = Publisher.objects.create(num_awards=1)
        cls.p2 = Publisher.objects.create(num_awards=0)
        cls.b1 = Book.objects.create(
            name="b1",
            publisher=cls.p1,
            pages=100,
            rating=4.5,
            price=10,
            contact=cls.a1,
            pubdate=datetime.date.today(),
        )
        cls.b1.authors.add(cls.a1)
        cls.b2 = Book.objects.create(
            name="b2",
            publisher=cls.p2,
            pages=1000,
            rating=3.2,
            price=50,
            contact=cls.a2,
            pubdate=datetime.date.today(),
        )
        cls.b2.authors.add(cls.a1, cls.a2)
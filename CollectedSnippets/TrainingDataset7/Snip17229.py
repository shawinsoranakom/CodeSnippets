def setUpTestData(cls):
        cls.a1 = Author.objects.create(name="Adrian Holovaty", age=34)
        cls.a2 = Author.objects.create(name="Jacob Kaplan-Moss", age=35)
        cls.a3 = Author.objects.create(name="James Bennett", age=34)
        cls.a4 = Author.objects.create(name="Peter Norvig", age=57)
        cls.a5 = Author.objects.create(name="Stuart Russell", age=46)
        p1 = Publisher.objects.create(name="Apress", num_awards=3)

        cls.b1 = Book.objects.create(
            isbn="159059725",
            pages=447,
            rating=4.5,
            price=Decimal("30.00"),
            contact=cls.a1,
            publisher=p1,
            pubdate=datetime.date(2007, 12, 6),
            name="The Definitive Guide to Django: Web Development Done Right",
        )
        cls.b2 = Book.objects.create(
            isbn="159059996",
            pages=300,
            rating=4.0,
            price=Decimal("29.69"),
            contact=cls.a3,
            publisher=p1,
            pubdate=datetime.date(2008, 6, 23),
            name="Practical Django Projects",
        )
        cls.b3 = Book.objects.create(
            isbn="013790395",
            pages=1132,
            rating=4.0,
            price=Decimal("82.80"),
            contact=cls.a4,
            publisher=p1,
            pubdate=datetime.date(1995, 1, 15),
            name="Artificial Intelligence: A Modern Approach",
        )
        cls.b4 = Book.objects.create(
            isbn="155860191",
            pages=946,
            rating=5.0,
            price=Decimal("75.00"),
            contact=cls.a4,
            publisher=p1,
            pubdate=datetime.date(1991, 10, 15),
            name=(
                "Paradigms of Artificial Intelligence Programming: Case Studies in "
                "Common Lisp"
            ),
        )
        cls.b1.authors.add(cls.a1, cls.a2)
        cls.b2.authors.add(cls.a3)
        cls.b3.authors.add(cls.a4, cls.a5)
        cls.b4.authors.add(cls.a4)

        Store.objects.create(
            name="Amazon.com",
            original_opening=datetime.datetime(1994, 4, 23, 9, 17, 42),
            friday_night_closing=datetime.time(23, 59, 59),
        )
        Store.objects.create(
            name="Books.com",
            original_opening=datetime.datetime(2001, 3, 15, 11, 23, 37),
            friday_night_closing=datetime.time(23, 59, 59),
        )
def setUpTestData(cls):
        cls.today = datetime.date.today()
        cls.tomorrow = cls.today + datetime.timedelta(days=1)
        cls.one_week_ago = cls.today - datetime.timedelta(days=7)
        if cls.today.month == 12:
            cls.next_month = cls.today.replace(year=cls.today.year + 1, month=1, day=1)
        else:
            cls.next_month = cls.today.replace(month=cls.today.month + 1, day=1)
        cls.next_year = cls.today.replace(year=cls.today.year + 1, month=1, day=1)

        # Users
        cls.alfred = User.objects.create_superuser(
            "alfred", "alfred@example.com", "password"
        )
        cls.bob = User.objects.create_user("bob", "bob@example.com")
        cls.lisa = User.objects.create_user("lisa", "lisa@example.com")

        # Departments
        cls.dev = Department.objects.create(code="DEV", description="Development")
        cls.design = Department.objects.create(code="DSN", description="Design")

        # Employees
        cls.john = Employee.objects.create(name="John Blue", department=cls.dev)
        cls.jack = Employee.objects.create(name="Jack Red", department=cls.design)

        # Books
        cls.djangonaut_book = Book.objects.create(
            title="Djangonaut: an art of living",
            year=2009,
            author=cls.alfred,
            is_best_seller=True,
            date_registered=cls.today,
            availability=True,
            category="non-fiction",
            employee=cls.john,
        )
        cls.bio_book = Book.objects.create(
            title="Django: a biography",
            year=1999,
            author=cls.alfred,
            is_best_seller=False,
            no=207,
            availability=False,
            category="fiction",
            employee=cls.john,
        )
        cls.django_book = Book.objects.create(
            title="The Django Book",
            year=None,
            author=cls.bob,
            is_best_seller=None,
            date_registered=cls.today,
            no=103,
            availability=True,
            employee=cls.jack,
        )
        cls.guitar_book = Book.objects.create(
            title="Guitar for dummies",
            year=2002,
            is_best_seller=True,
            date_registered=cls.one_week_ago,
            availability=None,
            category="",
        )
        cls.guitar_book.contributors.set([cls.bob, cls.lisa])
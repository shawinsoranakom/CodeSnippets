def setUpTestData(cls):
        cls.a1 = Author.objects.create(
            first_name="Joe", last_name="Smith", dob=date(1950, 9, 20)
        )
        cls.a2 = Author.objects.create(
            first_name="Jill", last_name="Doe", dob=date(1920, 4, 2)
        )
        cls.a3 = Author.objects.create(
            first_name="Bob", last_name="Smith", dob=date(1986, 1, 25)
        )
        cls.a4 = Author.objects.create(
            first_name="Bill", last_name="Jones", dob=date(1932, 5, 10)
        )
        cls.b1 = Book.objects.create(
            title="The awesome book",
            author=cls.a1,
            paperback=False,
            opening_line=(
                "It was a bright cold day in April and the clocks were striking "
                "thirteen."
            ),
        )
        cls.b2 = Book.objects.create(
            title="The horrible book",
            author=cls.a1,
            paperback=True,
            opening_line=(
                "On an evening in the latter part of May a middle-aged man "
                "was walking homeward from Shaston to the village of Marlott, "
                "in the adjoining Vale of Blakemore, or Blackmoor."
            ),
        )
        cls.b3 = Book.objects.create(
            title="Another awesome book",
            author=cls.a1,
            paperback=False,
            opening_line="A squat gray building of only thirty-four stories.",
        )
        cls.b4 = Book.objects.create(
            title="Some other book",
            author=cls.a3,
            paperback=True,
            opening_line="It was the day my grandmother exploded.",
        )
        cls.c1 = Coffee.objects.create(brand="dunkin doughnuts")
        cls.c2 = Coffee.objects.create(brand="starbucks")
        cls.r1 = Reviewer.objects.create()
        cls.r2 = Reviewer.objects.create()
        cls.r1.reviewed.add(cls.b2, cls.b3, cls.b4)
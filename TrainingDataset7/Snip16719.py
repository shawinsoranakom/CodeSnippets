def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )

        cls.s1 = State.objects.create(name="New York")
        cls.s2 = State.objects.create(name="Illinois")
        cls.s3 = State.objects.create(name="California")
        cls.c1 = City.objects.create(state=cls.s1, name="New York")
        cls.c2 = City.objects.create(state=cls.s2, name="Chicago")
        cls.c3 = City.objects.create(state=cls.s3, name="San Francisco")
        cls.r1 = Restaurant.objects.create(city=cls.c1, name="Italian Pizza")
        cls.r2 = Restaurant.objects.create(city=cls.c1, name="Boulevard")
        cls.r3 = Restaurant.objects.create(city=cls.c2, name="Chinese Dinner")
        cls.r4 = Restaurant.objects.create(city=cls.c2, name="Angels")
        cls.r5 = Restaurant.objects.create(city=cls.c2, name="Take Away")
        cls.r6 = Restaurant.objects.create(city=cls.c3, name="The Unknown Restaurant")
        cls.w1 = Worker.objects.create(work_at=cls.r1, name="Mario", surname="Rossi")
        cls.w2 = Worker.objects.create(
            work_at=cls.r1, name="Antonio", surname="Bianchi"
        )
        cls.w3 = Worker.objects.create(work_at=cls.r1, name="John", surname="Doe")
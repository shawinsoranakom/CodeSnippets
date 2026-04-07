def setUpTestData(cls):
        cls.a1 = Author.objects.create(name="a1", birthdate=date(1981, 2, 16))
        cls.a2 = Author.objects.create(name="a2", birthdate=date(2012, 2, 29))
        cls.a3 = Author.objects.create(name="a3", birthdate=date(2012, 1, 31))
        cls.a4 = Author.objects.create(name="a4", birthdate=date(2012, 3, 1))
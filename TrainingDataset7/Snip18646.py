def setUpTestData(cls):
        cls.p0 = Person.objects.create(first_name="a", last_name="a")
        cls.p1 = Person.objects.create(first_name="b", last_name="b")
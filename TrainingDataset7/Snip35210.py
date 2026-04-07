def setUpTestData(cls):
        cls.p1 = Person.objects.create(name="p1")
        cls.p2 = Person.objects.create(name="p2")
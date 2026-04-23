def setUpTestData(cls):
        cls.a, cls.b, cls.c, cls.d = [
            Person.objects.create(name=name)
            for name in ["Anne", "Bill", "Chuck", "David"]
        ]
        cls.a.friends.add(cls.b, cls.c)
        # Add m2m for Anne and Chuck in reverse direction.
        cls.d.friends.add(cls.a, cls.c)
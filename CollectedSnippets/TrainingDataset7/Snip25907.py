def setUpTestData(cls):
        cls.a, cls.b, cls.c, cls.d = [
            Person.objects.create(name=name)
            for name in ["Anne", "Bill", "Chuck", "David"]
        ]
        cls.a.colleagues.add(
            cls.b,
            cls.c,
            through_defaults={
                "first_meet": datetime.date(2013, 1, 5),
            },
        )
        # Add m2m for Anne and Chuck in reverse direction.
        cls.d.colleagues.add(
            cls.a,
            cls.c,
            through_defaults={
                "first_meet": datetime.date(2015, 6, 15),
            },
        )
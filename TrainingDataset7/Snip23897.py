def setUpTestData(cls):
        Person.objects.create(
            first_name="John", last_name="Lennon", birthday=date(1940, 10, 9)
        )
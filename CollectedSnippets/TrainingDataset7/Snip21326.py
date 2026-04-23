def setUpTestData(cls):
        cls.example_inc = Company.objects.create(
            name="Example Inc.",
            num_employees=2300,
            num_chairs=5,
            ceo=Employee.objects.create(firstname="Joe", lastname="Smith", salary=10),
        )
        cls.foobar_ltd = Company.objects.create(
            name="Foobar Ltd.",
            num_employees=3,
            num_chairs=4,
            based_in_eu=True,
            ceo=Employee.objects.create(firstname="Frank", lastname="Meyer", salary=20),
        )
        cls.max = Employee.objects.create(
            firstname="Max", lastname="Mustermann", salary=30
        )
        cls.gmbh = Company.objects.create(
            name="Test GmbH", num_employees=32, num_chairs=1, ceo=cls.max
        )
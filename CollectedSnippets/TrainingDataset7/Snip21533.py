def setUpTestData(cls):
        ceo = Employee.objects.create(firstname="Joe", lastname="Smith", salary=10)
        cls.eu_company = Company.objects.create(
            name="Example Inc.",
            num_employees=2300,
            num_chairs=5,
            ceo=ceo,
            based_in_eu=True,
        )
        cls.non_eu_company = Company.objects.create(
            name="Foobar Ltd.",
            num_employees=3,
            num_chairs=4,
            ceo=ceo,
            based_in_eu=False,
        )
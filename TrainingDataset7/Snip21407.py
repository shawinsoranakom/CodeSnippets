def setUpTestData(cls):
        ceo = Employee.objects.create(firstname="Just", lastname="Doit", salary=30)
        # MySQL requires that the values calculated for expressions don't pass
        # outside of the field's range, so it's inconvenient to use the values
        # in the more general tests.
        cls.c5020 = Company.objects.create(
            name="5020 Ltd", num_employees=50, num_chairs=20, ceo=ceo
        )
        cls.c5040 = Company.objects.create(
            name="5040 Ltd", num_employees=50, num_chairs=40, ceo=ceo
        )
        cls.c5050 = Company.objects.create(
            name="5050 Ltd", num_employees=50, num_chairs=50, ceo=ceo
        )
        cls.c5060 = Company.objects.create(
            name="5060 Ltd", num_employees=50, num_chairs=60, ceo=ceo
        )
        cls.c99300 = Company.objects.create(
            name="99300 Ltd", num_employees=99, num_chairs=300, ceo=ceo
        )
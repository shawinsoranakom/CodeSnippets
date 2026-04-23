def setUpTestData(cls):
        cls.dan = Employee.objects.create(
            employee_code=123,
            first_name="Dan",
            last_name="Jones",
        )
        cls.fran = Employee.objects.create(
            employee_code=456,
            first_name="Fran",
            last_name="Bones",
        )
        cls.business = Business.objects.create(name="Sears")
        cls.business.employees.add(cls.dan, cls.fran)
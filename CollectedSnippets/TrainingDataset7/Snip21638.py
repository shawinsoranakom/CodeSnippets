def setUpTestData(cls):
        classification = Classification.objects.create()
        Employee.objects.bulk_create(
            [
                Employee(
                    name=e[0],
                    salary=e[1],
                    department=e[2],
                    hire_date=e[3],
                    age=e[4],
                    bonus=Decimal(e[1]) / 400,
                    classification=classification,
                )
                for e in [
                    ("Jones", 45000, "Accounting", datetime.datetime(2005, 11, 1), 20),
                    (
                        "Williams",
                        37000,
                        "Accounting",
                        datetime.datetime(2009, 6, 1),
                        20,
                    ),
                    ("Jenson", 45000, "Accounting", datetime.datetime(2008, 4, 1), 20),
                    ("Adams", 50000, "Accounting", datetime.datetime(2013, 7, 1), 50),
                    ("Smith", 55000, "Sales", datetime.datetime(2007, 6, 1), 30),
                    ("Brown", 53000, "Sales", datetime.datetime(2009, 9, 1), 30),
                    ("Johnson", 40000, "Marketing", datetime.datetime(2012, 3, 1), 30),
                    ("Smith", 38000, "Marketing", datetime.datetime(2009, 10, 1), 20),
                    ("Wilkinson", 60000, "IT", datetime.datetime(2011, 3, 1), 40),
                    ("Moore", 34000, "IT", datetime.datetime(2013, 8, 1), 40),
                    ("Miller", 100000, "Management", datetime.datetime(2005, 6, 1), 40),
                    ("Johnson", 80000, "Management", datetime.datetime(2005, 7, 1), 50),
                ]
            ]
        )
        employees = list(Employee.objects.order_by("pk"))
        PastEmployeeDepartment.objects.bulk_create(
            [
                PastEmployeeDepartment(employee=employees[6], department="Sales"),
                PastEmployeeDepartment(employee=employees[10], department="IT"),
            ]
        )
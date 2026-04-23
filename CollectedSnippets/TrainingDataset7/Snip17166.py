def test_joined_transformed_annotation(self):
        Employee.objects.bulk_create(
            [
                Employee(
                    first_name="John",
                    last_name="Doe",
                    age=18,
                    store=self.s1,
                    salary=15000,
                ),
                Employee(
                    first_name="Jane",
                    last_name="Jones",
                    age=30,
                    store=self.s2,
                    salary=30000,
                ),
                Employee(
                    first_name="Jo",
                    last_name="Smith",
                    age=55,
                    store=self.s3,
                    salary=50000,
                ),
            ]
        )
        employees = Employee.objects.annotate(
            store_opened_year=F("store__original_opening__year"),
        )
        for employee in employees:
            self.assertEqual(
                employee.store_opened_year,
                employee.store.original_opening.year,
            )
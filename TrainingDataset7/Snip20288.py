def test_unique_pk(self):
        # The primary key must also be unique, so trying to create a new object
        # with the same primary key will fail.
        Employee.objects.create(
            employee_code=123, first_name="Frank", last_name="Jones"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Employee.objects.create(
                    employee_code=123, first_name="Fred", last_name="Jones"
                )
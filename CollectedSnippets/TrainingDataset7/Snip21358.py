def test_object_create_with_aggregate(self):
        # Aggregates are not allowed when inserting new data
        msg = (
            "Aggregate functions are not allowed in this query "
            "(num_employees=Max(Value(1)))."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Company.objects.create(
                name="Company",
                num_employees=Max(Value(1)),
                num_chairs=1,
                ceo=Employee.objects.create(
                    firstname="Just", lastname="Doit", salary=30
                ),
            )
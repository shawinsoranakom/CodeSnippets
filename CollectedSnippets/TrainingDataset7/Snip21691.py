def test_fail_insert(self):
        """Window expressions can't be used in an INSERT statement."""
        msg = (
            "Window expressions are not allowed in this query (salary=<Window: "
            "Sum(Value(10000)) OVER ()"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Employee.objects.create(
                name="Jameson",
                department="Management",
                hire_date=datetime.date(2007, 7, 1),
                salary=Window(expression=Sum(Value(10000))),
            )
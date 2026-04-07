def test_fail_update(self):
        """Window expressions can't be used in an UPDATE statement."""
        msg = (
            "Window expressions are not allowed in this query (salary=<Window: "
            "Max(Col(expressions_window_employee, expressions_window.Employee.salary)) "
            "OVER (PARTITION BY Col(expressions_window_employee, "
            "expressions_window.Employee.department))>)."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Employee.objects.filter(department="Management").update(
                salary=Window(expression=Max("salary"), partition_by="department"),
            )
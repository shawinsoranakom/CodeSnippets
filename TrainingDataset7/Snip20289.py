def test_zero_non_autoincrement_pk(self):
        Employee.objects.create(employee_code=0, first_name="Frank", last_name="Jones")
        employee = Employee.objects.get(pk=0)
        self.assertEqual(employee.employee_code, 0)
def test_lefthand_bitwise_xor_right_null(self):
        employee = Employee.objects.create(firstname="John", lastname="Doe", salary=48)
        Employee.objects.update(salary=F("salary").bitxor(None))
        employee.refresh_from_db()
        self.assertIsNone(employee.salary)
def test_lefthand_bitwise_xor_null(self):
        employee = Employee.objects.create(firstname="John", lastname="Doe")
        Employee.objects.update(salary=F("salary").bitxor(48))
        employee.refresh_from_db()
        self.assertIsNone(employee.salary)
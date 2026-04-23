def test_lefthand_modulo_null(self):
        # LH Modulo arithmetic on integers.
        Employee.objects.create(firstname="John", lastname="Doe", salary=None)
        qs = Employee.objects.annotate(modsalary=F("salary") % 20)
        self.assertIsNone(qs.get().salary)
def test_decimal_annotation(self):
        salary = Decimal(10) ** -Employee._meta.get_field("salary").decimal_places
        Employee.objects.create(
            first_name="Max",
            last_name="Paine",
            store=Store.objects.first(),
            age=23,
            salary=salary,
        )
        self.assertEqual(
            Employee.objects.annotate(new_salary=F("salary") / 10).get().new_salary,
            salary / 10,
        )
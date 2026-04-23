def test_ticket_16731_startswith_lookup(self):
        Employee.objects.create(firstname="John", lastname="Doe")
        e2 = Employee.objects.create(firstname="Jack", lastname="Jackson")
        e3 = Employee.objects.create(firstname="Jack", lastname="jackson")
        self.assertSequenceEqual(
            Employee.objects.filter(lastname__startswith=F("firstname")),
            [e2, e3] if connection.features.has_case_insensitive_like else [e2],
        )
        qs = Employee.objects.filter(lastname__istartswith=F("firstname")).order_by(
            "pk"
        )
        self.assertSequenceEqual(qs, [e2, e3])
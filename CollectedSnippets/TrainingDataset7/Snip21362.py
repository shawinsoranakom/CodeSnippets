def test_ticket_11722_iexact_lookup(self):
        Employee.objects.create(firstname="John", lastname="Doe")
        test = Employee.objects.create(firstname="Test", lastname="test")

        queryset = Employee.objects.filter(firstname__iexact=F("lastname"))
        self.assertSequenceEqual(queryset, [test])
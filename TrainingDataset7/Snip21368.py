def test_order_by_exists(self):
        mary = Employee.objects.create(
            firstname="Mary", lastname="Mustermann", salary=20
        )
        mustermanns_by_seniority = Employee.objects.filter(
            lastname="Mustermann"
        ).order_by(
            # Order by whether the employee is the CEO of a company
            Exists(Company.objects.filter(ceo=OuterRef("pk"))).desc()
        )
        self.assertSequenceEqual(mustermanns_by_seniority, [self.max, mary])
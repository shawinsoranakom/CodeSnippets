def test_ticket_18375_chained_filters(self):
        # F() expressions do not reuse joins from previous filter.
        qs = Employee.objects.filter(company_ceo_set__num_employees=F("pk")).filter(
            company_ceo_set__num_employees=F("company_ceo_set__num_employees")
        )
        self.assertEqual(str(qs.query).count("JOIN"), 2)
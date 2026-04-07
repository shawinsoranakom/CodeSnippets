def test_ticket_18375_join_reuse(self):
        # Reverse multijoin F() references and the lookup target the same join.
        # Pre #18375 the F() join was generated first and the lookup couldn't
        # reuse that join.
        qs = Employee.objects.filter(
            company_ceo_set__num_chairs=F("company_ceo_set__num_employees")
        )
        self.assertEqual(str(qs.query).count("JOIN"), 1)
def test_year_lte_sql(self):
        # This test will just check the generated SQL for __lte. This
        # doesn't require running on PostgreSQL and spots the most likely
        # error - not running YearLte SQL at all.
        baseqs = Author.objects.order_by("name")
        self.assertIn(
            "<= (2011 || ", str(baseqs.filter(birthdate__testyear__lte=2011).query)
        )
        self.assertIn("-12-31", str(baseqs.filter(birthdate__testyear__lte=2011).query))
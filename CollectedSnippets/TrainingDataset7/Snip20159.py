def test_postgres_year_exact(self):
        baseqs = Author.objects.order_by("name")
        self.assertIn("= (2011 || ", str(baseqs.filter(birthdate__testyear=2011).query))
        self.assertIn("-12-31", str(baseqs.filter(birthdate__testyear=2011).query))
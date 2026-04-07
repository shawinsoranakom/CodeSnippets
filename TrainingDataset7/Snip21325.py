def test_values_list_expression_flat(self):
        companies = Company.objects.values_list(F("ceo__salary"), flat=True)
        self.assertCountEqual(companies, (10, 20, 30))
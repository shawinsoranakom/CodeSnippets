def test_values_list_expression(self):
        companies = Company.objects.values_list("name", F("ceo__salary"))
        self.assertCountEqual(
            companies, [("Example Inc.", 10), ("Foobar Ltd.", 20), ("Test GmbH", 30)]
        )
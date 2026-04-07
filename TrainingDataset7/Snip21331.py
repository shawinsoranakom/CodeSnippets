def test_annotate_values_count(self):
        companies = Company.objects.annotate(foo=RawSQL("%s", ["value"]))
        self.assertEqual(companies.count(), 3)
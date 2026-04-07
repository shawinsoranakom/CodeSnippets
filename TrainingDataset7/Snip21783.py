def test_bulk_create_mixed_db_defaults_function(self):
        instances = [DBDefaultsFunction(), DBDefaultsFunction(year=2000)]
        DBDefaultsFunction.objects.bulk_create(instances)

        years = DBDefaultsFunction.objects.values_list("year", flat=True)
        self.assertCountEqual(years, [2000, datetime.now(UTC).year])
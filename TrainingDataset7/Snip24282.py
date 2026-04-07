def test_gis_lookups_with_complex_expressions(self):
        multiple_arg_lookups = {
            "dwithin",
            "relate",
        }  # These lookups are tested elsewhere.
        lookups = connection.ops.gis_operators.keys() - multiple_arg_lookups
        self.assertTrue(lookups, "No lookups found")
        for lookup in lookups:
            with self.subTest(lookup):
                City.objects.filter(
                    **{"point__" + lookup: functions.Union("point", "point")}
                ).exists()
def test_filtering_on_rawsql_that_is_boolean(self):
        self.assertEqual(
            Company.objects.filter(
                RawSQL("num_employees > %s", (3,), output_field=BooleanField()),
            ).count(),
            2,
        )
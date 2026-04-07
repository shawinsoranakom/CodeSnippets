def test_order_by_multiline_sql(self):
        raw_order_by = (
            RawSQL(
                """
                CASE WHEN num_employees > 1000
                     THEN num_chairs
                     ELSE 0 END
                """,
                [],
            ).desc(),
            RawSQL(
                """
                CASE WHEN num_chairs > 1
                     THEN 1
                     ELSE 0 END
                """,
                [],
            ).asc(),
        )
        for qs in (
            Company.objects.all(),
            Company.objects.distinct(),
        ):
            with self.subTest(qs=qs):
                self.assertSequenceEqual(
                    qs.order_by(*raw_order_by),
                    [self.example_inc, self.gmbh, self.foobar_ltd],
                )
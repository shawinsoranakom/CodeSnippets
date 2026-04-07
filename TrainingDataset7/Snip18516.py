def test_set_time_zone_sql(self):
        self.assertEqual(self.ops.set_time_zone_sql(), "")
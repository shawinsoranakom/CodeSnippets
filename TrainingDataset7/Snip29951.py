def test_loading(self):
        instance = list(serializers.deserialize("json", self.test_data))[0].object
        self.assertEqual(instance.ints, NumericRange(0, 10))
        self.assertEqual(instance.decimals, NumericRange(empty=True))
        self.assertIsNone(instance.bigints)
        self.assertEqual(instance.dates, DateRange(self.lower_date, self.upper_date))
        self.assertEqual(
            instance.timestamps, DateTimeTZRange(self.lower_dt, self.upper_dt)
        )
        self.assertEqual(
            instance.timestamps_closed_bounds,
            DateTimeTZRange(self.lower_dt, self.upper_dt, bounds="()"),
        )
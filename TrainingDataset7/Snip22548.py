def test_durationfield_integer_value(self):
        f = DurationField()
        self.assertEqual(datetime.timedelta(0, 10800), f.clean(10800))
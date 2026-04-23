def test_durationfield_prepare_value(self):
        field = DurationField()
        td = datetime.timedelta(minutes=15, seconds=30)
        self.assertEqual(field.prepare_value(td), duration_string(td))
        self.assertEqual(field.prepare_value("arbitrary"), "arbitrary")
        self.assertIsNone(field.prepare_value(None))
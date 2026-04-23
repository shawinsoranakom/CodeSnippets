def test_fractional_seconds(self):
        value = datetime.timedelta(seconds=2.05)
        d = DurationModel.objects.create(field=value)
        d.refresh_from_db()
        self.assertEqual(d.field, value)
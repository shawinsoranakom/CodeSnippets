def test_fixedoffset_timedelta(self):
        delta = datetime.timedelta(hours=1)
        self.assertEqual(timezone.get_fixed_timezone(delta).utcoffset(None), delta)
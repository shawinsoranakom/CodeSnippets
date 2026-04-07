def test_adapt_timefield_value_unaware(self):
        now = timezone.now()
        self.assertEqual(self.ops.adapt_timefield_value(now), str(now))
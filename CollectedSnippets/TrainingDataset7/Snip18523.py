def test_adapt_unknown_value_time(self):
        value = timezone.now().time()
        self.assertEqual(
            self.ops.adapt_unknown_value(value), self.ops.adapt_timefield_value(value)
        )
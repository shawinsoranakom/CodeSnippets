def test_adapt_timefield_value_none(self):
        self.assertIsNone(self.ops.adapt_timefield_value(None))
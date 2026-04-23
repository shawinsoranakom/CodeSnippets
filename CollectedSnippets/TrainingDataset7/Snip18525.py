def test_adapt_datetimefield_value_none(self):
        self.assertIsNone(self.ops.adapt_datetimefield_value(None))
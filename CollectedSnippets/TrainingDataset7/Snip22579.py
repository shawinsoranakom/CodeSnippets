def test_floatfield_2(self):
        f = FloatField(required=False)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))
        self.assertEqual(1.0, f.clean("1"))
        self.assertIsNone(f.max_value)
        self.assertIsNone(f.min_value)
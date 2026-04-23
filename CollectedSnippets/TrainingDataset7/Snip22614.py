def test_integerfield_big_num(self):
        f = IntegerField()
        self.assertEqual(9223372036854775808, f.clean(9223372036854775808))
        self.assertEqual(9223372036854775808, f.clean("9223372036854775808"))
        self.assertEqual(9223372036854775808, f.clean("9223372036854775808.0"))
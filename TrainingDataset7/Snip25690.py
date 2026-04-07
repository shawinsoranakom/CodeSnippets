def test_sense(self):
        f_false = CallbackFilter(lambda r: False)
        f_true = CallbackFilter(lambda r: True)

        self.assertFalse(f_false.filter("record"))
        self.assertTrue(f_true.filter("record"))
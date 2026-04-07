def test_integerfield_unicode_number(self):
        f = IntegerField()
        self.assertEqual(50, f.clean("５０"))
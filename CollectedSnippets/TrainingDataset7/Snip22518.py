def test_datefield_2(self):
        f = DateField(required=False)
        self.assertIsNone(f.clean(None))
        self.assertEqual("None", repr(f.clean(None)))
        self.assertIsNone(f.clean(""))
        self.assertEqual("None", repr(f.clean("")))
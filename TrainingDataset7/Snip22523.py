def test_datefield_strptime(self):
        """field.strptime() doesn't raise a UnicodeEncodeError (#16123)"""
        f = DateField()
        try:
            f.strptime("31 мая 2011", "%d-%b-%y")
        except Exception as e:
            # assertIsInstance or assertRaises cannot be used because
            # UnicodeEncodeError is a subclass of ValueError
            self.assertEqual(e.__class__, ValueError)
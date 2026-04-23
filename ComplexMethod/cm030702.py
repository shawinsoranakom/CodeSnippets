def test_numeric(self):
        self.assertEqual(self.db.numeric('A',None), None)
        self.assertEqual(self.db.numeric('9'), 9)
        self.assertEqual(self.db.numeric('\u215b'), 0.125)
        self.assertEqual(self.db.numeric('\u2468'), 9.0)
        self.assertEqual(self.db.numeric('\U00020000', None), None)

        # New in 4.1.0
        self.assertEqual(self.db.numeric('\U0001012A', None), None if self.old else 9000)
        # Changed in 4.1.0
        self.assertEqual(self.db.numeric('\u5793', None), 1e20 if self.old else None)
        # New in 5.0.0
        self.assertEqual(self.db.numeric('\u07c0', None), None if self.old else 0.0)
        # New in 5.1.0
        self.assertEqual(self.db.numeric('\ua627', None), None if self.old else 7.0)
        # Changed in 5.2.0
        self.assertEqual(self.db.numeric('\u09f6'), 3.0 if self.old else 3/16)
        # New in 6.0.0
        self.assertEqual(self.db.numeric('\u0b72', None), None if self.old else 0.25)
        # New in 12.0.0
        self.assertEqual(self.db.numeric('\U0001ed3c', None), None if self.old else 0.5)
        # New in 13.0.0
        self.assertEqual(self.db.numeric('\U0001fbf9', None), None if self.old else 9)
        # New in 14.0.0
        self.assertEqual(self.db.numeric('\U00016ac9', None), None if self.old else 9)
        # New in 15.0.0
        self.assertEqual(self.db.numeric('\U0001e4f9', None), None if self.old else 9)

        self.assertRaises(TypeError, self.db.numeric)
        self.assertRaises(TypeError, self.db.numeric, 'xx')
        self.assertRaises(ValueError, self.db.numeric, 'x')
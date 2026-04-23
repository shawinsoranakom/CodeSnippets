def test_category(self):
        self.assertEqual(self.db.category('\uFFFE'), 'Cn')
        self.assertEqual(self.db.category('a'), 'Ll')
        self.assertEqual(self.db.category('A'), 'Lu')
        self.assertEqual(self.db.category('\U00020000'), 'Lo')

        # New in 4.1.0
        self.assertEqual(self.db.category('\U0001012A'), 'Cn' if self.old else 'No')
        self.assertEqual(self.db.category('\U000e01ef'), 'Cn' if self.old else 'Mn')
        # New in 5.1.0
        self.assertEqual(self.db.category('\u0374'), 'Sk' if self.old else 'Lm')
        # Changed in 13.0.0
        self.assertEqual(self.db.category('\u0b55'), 'Cn' if self.old else 'Mn')
        self.assertEqual(self.db.category('\U0003134a'), 'Cn' if self.old else 'Lo')
        # Changed in 14.0.0
        self.assertEqual(self.db.category('\u061d'), 'Cn' if self.old else 'Po')
        self.assertEqual(self.db.category('\U0002b738'), 'Cn' if self.old else 'Lo')
        # Changed in 15.0.0
        self.assertEqual(self.db.category('\u0cf3'), 'Cn' if self.old else 'Mc')
        self.assertEqual(self.db.category('\U000323af'), 'Cn' if self.old else 'Lo')

        self.assertRaises(TypeError, self.db.category)
        self.assertRaises(TypeError, self.db.category, 'xx')
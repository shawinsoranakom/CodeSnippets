def test_bidirectional(self):
        self.assertEqual(self.db.bidirectional('\uFFFE'), 'BN')
        self.assertEqual(self.db.bidirectional(' '), 'WS')
        self.assertEqual(self.db.bidirectional('A'), 'L')
        self.assertEqual(self.db.bidirectional('\U00020000'), 'L')

        # New in 4.1.0
        self.assertEqual(self.db.bidirectional('+'), 'ET' if self.old else 'ES')
        self.assertEqual(self.db.bidirectional('\u0221'), '' if self.old else 'L')
        self.assertEqual(self.db.bidirectional('\U000e01ef'), '' if self.old else 'NSM')
        # New in 13.0.0
        self.assertEqual(self.db.bidirectional('\u0b55'), '' if self.old else 'NSM')
        self.assertEqual(self.db.bidirectional('\U0003134a'), '' if self.old else 'L')
        # New in 14.0.0
        self.assertEqual(self.db.bidirectional('\u061d'), '' if self.old else 'AL')
        self.assertEqual(self.db.bidirectional('\U0002b738'), '' if self.old else 'L')
        # New in 15.0.0
        self.assertEqual(self.db.bidirectional('\u0cf3'), '' if self.old else 'L')
        self.assertEqual(self.db.bidirectional('\U000323af'), '' if self.old else 'L')
        # New in 16.0.0
        self.assertEqual(self.db.bidirectional('\u0897'), '' if self.old else 'NSM')
        self.assertEqual(self.db.bidirectional('\U0001fbef'), '' if self.old else 'ON')
        # New in 17.0.0
        self.assertEqual(self.db.bidirectional('\u088f'), '' if self.old else 'AL')
        self.assertEqual(self.db.bidirectional('\U0001fbfa'), '' if self.old else 'ON')

        self.assertRaises(TypeError, self.db.bidirectional)
        self.assertRaises(TypeError, self.db.bidirectional, 'xx')
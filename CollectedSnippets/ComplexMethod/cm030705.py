def test_decomposition(self):
        self.assertEqual(self.db.decomposition('\uFFFE'),'')
        self.assertEqual(self.db.decomposition('\u00bc'), '<fraction> 0031 2044 0034')

        # New in 4.1.0
        self.assertEqual(self.db.decomposition('\u03f9'), '' if self.old else '<compat> 03A3')
        # New in 13.0.0
        self.assertEqual(self.db.decomposition('\uab69'), '' if self.old else '<super> 028D')
        self.assertEqual(self.db.decomposition('\U00011938'), '' if self.old else '11935 11930')
        self.assertEqual(self.db.decomposition('\U0001fbf9'), '' if self.old else '<font> 0039')
        # New in 14.0.0
        self.assertEqual(self.db.decomposition('\ua7f2'), '' if self.old else '<super> 0043')
        self.assertEqual(self.db.decomposition('\U000107ba'), '' if self.old else '<super> 1DF1E')
        # New in 15.0.0
        self.assertEqual(self.db.decomposition('\U0001e06d'), '' if self.old else '<super> 04B1')
        # New in 16.0.0
        self.assertEqual(self.db.decomposition('\U0001CCD6'), '' if self.old else '<font> 0041')
        # New in 17.0.0
        self.assertEqual(self.db.decomposition('\uA7F1'), '' if self.old else '<super> 0053')

        # Hangul characters
        self.assertEqual(self.db.decomposition('\uAC00'), '1100 1161')
        self.assertEqual(self.db.decomposition('\uD4DB'), '1111 1171 11B6')
        self.assertEqual(self.db.decomposition('\uC2F8'), '110A 1161')
        self.assertEqual(self.db.decomposition('\uD7A3'), '1112 1175 11C2')

        self.assertRaises(TypeError, self.db.decomposition)
        self.assertRaises(TypeError, self.db.decomposition, 'xx')
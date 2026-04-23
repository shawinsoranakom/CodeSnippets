def test_east_asian_width(self):
        eaw = self.db.east_asian_width
        self.assertRaises(TypeError, eaw, b'a')
        self.assertRaises(TypeError, eaw, bytearray())
        self.assertRaises(TypeError, eaw, '')
        self.assertRaises(TypeError, eaw, 'ra')
        self.assertEqual(eaw('\x1e'), 'N')
        self.assertEqual(eaw('\x20'), 'Na')
        self.assertEqual(eaw('\uC894'), 'W')
        self.assertEqual(eaw('\uFF66'), 'H')
        self.assertEqual(eaw('\uFF1F'), 'F')
        self.assertEqual(eaw('\u2010'), 'A')
        self.assertEqual(eaw('\U00020000'), 'W')

        # New in 4.1.0
        self.assertEqual(eaw('\u0350'), 'N' if self.old else 'A')
        self.assertEqual(eaw('\U000e01ef'), 'N' if self.old else 'A')
        # New in 5.2.0
        self.assertEqual(eaw('\u115a'), 'N' if self.old else 'W')
        # New in 9.0.0
        self.assertEqual(eaw('\u231a'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\u2614'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0001f19a'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0001f991'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0001f9c0'), 'N' if self.old else 'W')
        # New in 12.0.0
        self.assertEqual(eaw('\u32ff'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0001fa95'), 'N' if self.old else 'W')
        # New in 13.0.0
        self.assertEqual(eaw('\u31bb'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0003134a'), 'N' if self.old else 'W')
        # New in 14.0.0
        self.assertEqual(eaw('\u9ffd'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0002b738'), 'N' if self.old else 'W')
        # New in 15.0.0
        self.assertEqual(eaw('\U000323af'), 'N' if self.old else 'W')
        # New in 16.0.0
        self.assertEqual(eaw('\u2630'), 'N' if self.old else 'W')
        self.assertEqual(eaw('\U0001FAE9'), 'N' if self.old else 'W')
        # New in 17.0.0
        self.assertEqual(eaw('\U00016FF2'), 'N' if self.old else 'W')
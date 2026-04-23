def test_combining(self):
        self.assertEqual(self.db.combining('\uFFFE'), 0)
        self.assertEqual(self.db.combining('a'), 0)
        self.assertEqual(self.db.combining('\u20e1'), 230)
        self.assertEqual(self.db.combining('\U00020000'), 0)

        # New in 4.1.0
        self.assertEqual(self.db.combining('\u0350'), 0 if self.old else 230)
        # New in 9.0.0
        self.assertEqual(self.db.combining('\U0001e94a'), 0 if self.old else 7)
        # New in 13.0.0
        self.assertEqual(self.db.combining('\u1abf'), 0 if self.old else 220)
        self.assertEqual(self.db.combining('\U00016ff1'), 0 if self.old else 6)
        # New in 14.0.0
        self.assertEqual(self.db.combining('\u0c3c'), 0 if self.old else 7)
        self.assertEqual(self.db.combining('\U0001e2ae'), 0 if self.old else 230)
        # New in 15.0.0
        self.assertEqual(self.db.combining('\U00010efd'), 0 if self.old else 220)
        # New in 16.0.0
        self.assertEqual(self.db.combining('\u0897'), 0 if self.old else 230)
        # New in 17.0.0
        self.assertEqual(self.db.combining('\u1ACF'), 0 if self.old else 230)

        self.assertRaises(TypeError, self.db.combining)
        self.assertRaises(TypeError, self.db.combining, 'xx')
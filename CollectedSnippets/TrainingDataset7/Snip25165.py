def test_round_away_from_one(self):
        tests = [
            (0, 0),
            (0.0, 0),
            (0.25, 0),
            (0.5, 0),
            (0.75, 0),
            (1, 1),
            (1.0, 1),
            (1.25, 2),
            (1.5, 2),
            (1.75, 2),
            (-0.0, 0),
            (-0.25, -1),
            (-0.5, -1),
            (-0.75, -1),
            (-1, -1),
            (-1.0, -1),
            (-1.25, -2),
            (-1.5, -2),
            (-1.75, -2),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertEqual(round_away_from_one(value), expected)
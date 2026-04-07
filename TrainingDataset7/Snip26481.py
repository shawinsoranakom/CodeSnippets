def test_bisect_keep_left(self):
        self.assertEqual(bisect_keep_left([1, 1, 1], fn=lambda arr: sum(arr) != 2), 2)
        self.assertEqual(bisect_keep_left([1, 1, 1], fn=lambda arr: sum(arr) != 0), 0)
        self.assertEqual(bisect_keep_left([], fn=lambda arr: sum(arr) != 0), 0)
def test_bisect_keep_right(self):
        self.assertEqual(bisect_keep_right([1, 1, 1], fn=lambda arr: sum(arr) != 2), 1)
        self.assertEqual(
            bisect_keep_right([1, 1, 1, 1], fn=lambda arr: sum(arr) != 2), 2
        )
        self.assertEqual(
            bisect_keep_right([1, 1, 1, 1, 1], fn=lambda arr: sum(arr) != 1), 4
        )
        self.assertEqual(bisect_keep_right([], fn=lambda arr: sum(arr) != 0), 0)
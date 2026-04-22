def test_index_numpy_array(self):
        self.assertEqual(index_(np.array([1, 2, 3, 4]), 1), 0)
        self.assertEqual(index_(np.array([1, 2, 3, 4]), 4), 3)
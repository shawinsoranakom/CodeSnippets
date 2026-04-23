def test_index_numpy_array_fails(self):
        with self.assertRaises(ValueError):
            index_(np.array([1, 2, 3, 4]), 5)
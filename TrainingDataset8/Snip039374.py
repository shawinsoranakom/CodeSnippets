def test_numpy(self):
        np1 = np.zeros(10)
        np2 = np.zeros(11)
        np3 = np.zeros(10)

        self.assertEqual(get_hash(np1), get_hash(np3))
        self.assertNotEqual(get_hash(np1), get_hash(np2))

        np4 = np.zeros(_NP_SIZE_LARGE)
        np5 = np.zeros(_NP_SIZE_LARGE)

        self.assertEqual(get_hash(np4), get_hash(np5))
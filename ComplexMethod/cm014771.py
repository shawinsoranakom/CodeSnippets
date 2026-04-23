def test_scalar(self):
        res = make_np(1.1)
        self.assertIsInstance(res, np.ndarray) and self.assertEqual(res.shape, (1,))
        res = make_np(1 << 64 - 1)  # uint64_max
        self.assertIsInstance(res, np.ndarray) and self.assertEqual(res.shape, (1,))
        res = make_np(np.float16(1.00000087))
        self.assertIsInstance(res, np.ndarray) and self.assertEqual(res.shape, (1,))
        if not IS_MACOS and not IS_WINDOWS:
            res = make_np(np.float128(1.00008 + 9))
            self.assertIsInstance(res, np.ndarray) and self.assertEqual(res.shape, (1,))
        res = make_np(np.int64(100000000000))
        self.assertIsInstance(res, np.ndarray) and self.assertEqual(res.shape, (1,))
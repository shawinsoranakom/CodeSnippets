def test_hsplit(self):
        x = np.arange(18).reshape((3, 6))

        self.assertIsInstance(knp.hsplit(x, 3), list)

        for split_knp, split_np in zip(knp.hsplit(x, 3), np.hsplit(x, 3)):
            self.assertAllClose(split_knp, split_np)

        for split_knp, split_np in zip(knp.Hsplit(3)(x), np.hsplit(x, 3)):
            self.assertAllClose(split_knp, split_np)

        indices = [1, 3, 5]

        # Compare each split
        for split_knp, split_np in zip(
            knp.hsplit(x, indices), np.hsplit(x, indices)
        ):
            self.assertAllClose(split_knp, split_np)

        for split_knp, split_np in zip(
            knp.Hsplit(indices)(x), np.hsplit(x, indices)
        ):
            self.assertAllClose(split_knp, split_np)

        with self.assertRaises(Exception):
            knp.hsplit(x, 4)

        x_kr = knp.array(x)
        indices_kr = knp.array(indices)
        indices_np = np.array(indices)

        for split_knp, split_np in zip(
            knp.hsplit(x_kr, indices_kr), np.hsplit(x, indices_np)
        ):
            self.assertAllClose(split_knp, split_np)

        # Test 1D case
        x_1d = np.arange(10)
        indices_1d = [2, 5, 9]

        self.assertIsInstance(knp.hsplit(x_1d, 2), list)

        for split_knp, split_np in zip(knp.hsplit(x_1d, 2), np.hsplit(x_1d, 2)):
            self.assertAllClose(split_knp, split_np)

        for split_knp, split_np in zip(knp.Hsplit(2)(x_1d), np.hsplit(x_1d, 2)):
            self.assertAllClose(split_knp, split_np)

        for split_knp, split_np in zip(
            knp.hsplit(x_1d, indices_1d), np.hsplit(x_1d, indices_1d)
        ):
            self.assertAllClose(split_knp, split_np)

        for split_knp, split_np in zip(
            knp.Hsplit(indices_1d)(x_1d), np.hsplit(x_1d, indices_1d)
        ):
            self.assertAllClose(split_knp, split_np)

        with self.assertRaises(Exception):
            knp.hsplit(x_1d, 3)

        x_kr = knp.array(x_1d)
        indices_kr = knp.array(indices_1d)
        indices_np = np.array(indices_1d)

        for split_knp, split_np in zip(
            knp.hsplit(x_kr, indices_kr), np.hsplit(x_1d, indices_np)
        ):
            self.assertAllClose(split_knp, split_np)
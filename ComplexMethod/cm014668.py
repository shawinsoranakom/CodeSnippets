def test_unbatch_iterdatapipe(self):
        target_length = 6
        prebatch_dp = dp.iter.IterableWrapper(range(target_length))

        # Functional Test: Unbatch DataPipe should be the same as pre-batch DataPipe
        input_dp = prebatch_dp.batch(3)
        unbatch_dp = input_dp.unbatch()
        self.assertEqual(len(list(unbatch_dp)), target_length)  # __len__ is as expected
        for i, res in zip(range(target_length), unbatch_dp):
            self.assertEqual(i, res)

        # Functional Test: unbatch works for an input with nested levels
        input_dp = dp.iter.IterableWrapper([[0, 1, 2], [3, 4, 5]])
        unbatch_dp = input_dp.unbatch()
        self.assertEqual(len(list(unbatch_dp)), target_length)
        for i, res in zip(range(target_length), unbatch_dp):
            self.assertEqual(i, res)

        input_dp = dp.iter.IterableWrapper([[[0, 1], [2, 3]], [[4, 5], [6, 7]]])

        # Functional Test: unbatch works for an input with nested levels
        unbatch_dp = input_dp.unbatch()
        expected_dp = [[0, 1], [2, 3], [4, 5], [6, 7]]
        self.assertEqual(len(list(unbatch_dp)), 4)
        for j, res in zip(expected_dp, unbatch_dp):
            self.assertEqual(j, res)

        # Functional Test: unbatching multiple levels at the same time
        unbatch_dp = input_dp.unbatch(unbatch_level=2)
        expected_dp2 = [0, 1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(len(list(unbatch_dp)), 8)
        for i, res in zip(expected_dp2, unbatch_dp):
            self.assertEqual(i, res)

        # Functional Test: unbatching all levels at the same time
        unbatch_dp = input_dp.unbatch(unbatch_level=-1)
        self.assertEqual(len(list(unbatch_dp)), 8)
        for i, res in zip(expected_dp2, unbatch_dp):
            self.assertEqual(i, res)

        # Functional Test: raises error when input unbatch_level is less than -1
        input_dp = dp.iter.IterableWrapper([[0, 1, 2], [3, 4, 5]])
        with self.assertRaises(ValueError):
            unbatch_dp = input_dp.unbatch(unbatch_level=-2)
            for i in unbatch_dp:
                print(i)

        # Functional Test: raises error when input unbatch_level is too high
        with self.assertRaises(IndexError):
            unbatch_dp = input_dp.unbatch(unbatch_level=5)
            for i in unbatch_dp:
                print(i)

        # Reset Test: unbatch_dp resets properly
        input_dp = dp.iter.IterableWrapper([[0, 1, 2], [3, 4, 5]])
        unbatch_dp = input_dp.unbatch(unbatch_level=-1)
        n_elements_before_reset = 3
        res_before_reset, res_after_reset = reset_after_n_next_calls(
            unbatch_dp, n_elements_before_reset
        )
        self.assertEqual([0, 1, 2], res_before_reset)
        self.assertEqual([0, 1, 2, 3, 4, 5], res_after_reset)
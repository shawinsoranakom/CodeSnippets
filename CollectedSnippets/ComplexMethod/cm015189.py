def test_rearrange_permutations(self) -> None:
        # tests random permutation of axes against two independent numpy ways
        for n_axes in range(1, 10):
            input = torch.arange(2**n_axes).reshape([2] * n_axes)
            permutation = np.random.permutation(n_axes)
            left_expression = " ".join("i" + str(axis) for axis in range(n_axes))
            right_expression = " ".join("i" + str(axis) for axis in permutation)
            expression = left_expression + " -> " + right_expression
            result = rearrange(input, expression)

            for pick in np.random.randint(0, 2, [10, n_axes]):
                self.assertEqual(input[tuple(pick)], result[tuple(pick[permutation])])

        for n_axes in range(1, 10):
            input = torch.arange(2**n_axes).reshape([2] * n_axes)
            permutation = np.random.permutation(n_axes)
            left_expression = " ".join("i" + str(axis) for axis in range(n_axes)[::-1])
            right_expression = " ".join("i" + str(axis) for axis in permutation[::-1])
            expression = left_expression + " -> " + right_expression
            result = rearrange(input, expression)
            self.assertEqual(result.shape, input.shape)
            expected_result = torch.zeros_like(input)
            for original_axis, result_axis in enumerate(permutation):
                expected_result |= ((input >> original_axis) & 1) << result_axis

            torch.testing.assert_close(result, expected_result)
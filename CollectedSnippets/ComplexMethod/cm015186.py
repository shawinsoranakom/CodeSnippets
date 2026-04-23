def test_broadcast_shapes(self, device):
        examples = [(), (1,), (2,), (1, 1), (3, 1), (3, 2), (4, 1, 1), (4, 3, 2)]
        for s0 in examples:
            x0 = torch.randn(s0)
            expected = torch.broadcast_tensors(x0)[0].shape
            actual = torch.broadcast_shapes(s0)
            self.assertEqual(expected, actual)

            for s1 in examples:
                x1 = torch.randn(s1)
                expected = torch.broadcast_tensors(x0, x1)[0].shape
                actual = torch.broadcast_shapes(s0, s1)
                self.assertEqual(expected, actual)

        inputs_list = [[1, 4], [4, 1], [1, 1, 3]]
        for integral_inputs in inputs_list:
            res1 = torch.broadcast_shapes(*integral_inputs)
            res2 = torch.broadcast_tensors(*map(torch.empty, integral_inputs))[0].shape
            self.assertEqual(res1, res2)

        inputs_with_neg_vals = [[1, 1, -12], [-1, 1], [-11]]
        for integral_inputs_with_neg_vals in inputs_with_neg_vals:
            with self.assertRaisesRegex(
                ValueError, "Attempting to broadcast a dimension with negative length!"
            ):
                torch.broadcast_shapes(*integral_inputs_with_neg_vals)

        integral_inputs_error_case = [(3, 5), (2, 4, 1)]
        for error_input in integral_inputs_error_case:
            with self.assertRaisesRegex(
                RuntimeError,
                ".*expected shape should be broadcastable to*",
            ):
                torch.broadcast_shapes(*error_input)

        negative_inputs = [(-1,), (1, -12), (4, -11), (-4, 1), (1, 1, -2)]
        for s0 in negative_inputs:
            with self.assertRaisesRegex(
                ValueError, "Attempting to broadcast a dimension with negative length!"
            ):
                torch.broadcast_shapes(s0)

            for s1 in negative_inputs:
                with self.assertRaisesRegex(
                    ValueError,
                    "Attempting to broadcast a dimension with negative length!",
                ):
                    torch.broadcast_shapes(s0, s1)

        float_inputs_error_case = [(1.1, 2.0), (1.1, 1.0)]
        for error_case in float_inputs_error_case:
            for float_input in error_case:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Input shapes "
                    "should be of type ints, a tuple of ints, or a list of ints",
                ):
                    torch.broadcast_shapes(float_input)

        diff_input_types = [(1, (5,)), (3, (1,)), (1, (3, 4))]
        for s0 in diff_input_types:
            res1 = torch.broadcast_shapes(*s0)
            res2 = torch.broadcast_tensors(*map(torch.empty, s0))[0].shape
            self.assertEqual(res1, res2)
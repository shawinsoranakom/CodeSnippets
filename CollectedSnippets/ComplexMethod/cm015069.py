def run_test(device, dtype):
            x = torch.tensor(
                [
                    [[1.0, 1.0], [0.0, 1.0], [2.0, 1.0], [0.0, 1.0]],
                    [[1.0, 1.0], [0.0, 1.0], [2.0, 1.0], [0.0, 1.0]],
                ],
                dtype=dtype,
                device=device,
            )
            x_empty = torch.empty(5, 0, dtype=dtype, device=device)
            x_ill_formed_empty = torch.empty(5, 0, 0, dtype=dtype, device=device)
            x_ill_formed_empty_another = torch.empty(
                5, 0, 5, dtype=dtype, device=device
            )
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                x_nan = torch.tensor(
                    [float("nan"), 0, 0, float("nan"), float("nan"), 1],
                    dtype=dtype,
                    device=device,
                )
            expected_unique_dim0 = torch.tensor(
                [[[1.0, 1.0], [0.0, 1.0], [2.0, 1.0], [0.0, 1.0]]],
                dtype=dtype,
                device=device,
            )
            expected_inverse_dim0 = torch.tensor([0, 0])
            expected_counts_dim0 = torch.tensor([2])
            expected_unique_dim1 = torch.tensor(
                [
                    [[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]],
                    [[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]],
                ],
                dtype=dtype,
                device=device,
            )
            expected_unique_dim1_bool = torch.tensor(
                [[[False, True], [True, True]], [[False, True], [True, True]]],
                dtype=torch.bool,
                device=device,
            )
            expected_inverse_dim1 = torch.tensor([1, 0, 2, 0])
            expected_inverse_dim1_bool = torch.tensor([1, 0, 1, 0])
            expected_counts_dim1 = torch.tensor([2, 1, 1])
            expected_counts_dim1_bool = torch.tensor([2, 2])
            expected_unique_dim2 = torch.tensor(
                [
                    [[1.0, 1.0], [0.0, 1.0], [2.0, 1.0], [0.0, 1.0]],
                    [[1.0, 1.0], [0.0, 1.0], [2.0, 1.0], [0.0, 1.0]],
                ],
                dtype=dtype,
                device=device,
            )
            expected_inverse_dim2 = torch.tensor([0, 1])
            expected_counts_dim2 = torch.tensor([1, 1])
            expected_unique_empty = torch.empty(5, 0, dtype=dtype, device=device)
            expected_inverse_empty = torch.tensor([], dtype=torch.long, device=device)
            expected_counts_empty = torch.tensor([], dtype=torch.long, device=device)
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                expected_unique_nan = torch.tensor(
                    [float("nan"), 0, float("nan"), float("nan"), 1],
                    dtype=dtype,
                    device=device,
                )
                expected_inverse_nan = torch.tensor(
                    [0, 1, 1, 2, 3, 4], dtype=torch.long, device=device
                )
                expected_counts_nan = torch.tensor(
                    [1, 2, 1, 1, 1], dtype=torch.long, device=device
                )
            # dim0
            x_unique = torch.unique(x, dim=0)
            self.assertEqual(expected_unique_dim0, x_unique)

            x_unique, x_inverse = torch.unique(x, return_inverse=True, dim=0)
            self.assertEqual(expected_unique_dim0, x_unique)
            self.assertEqual(expected_inverse_dim0, x_inverse)

            x_unique, x_counts = torch.unique(
                x, return_inverse=False, return_counts=True, dim=0
            )
            self.assertEqual(expected_unique_dim0, x_unique)
            self.assertEqual(expected_counts_dim0, x_counts)

            x_unique, x_inverse, x_counts = torch.unique(
                x, return_inverse=True, return_counts=True, dim=0
            )
            self.assertEqual(expected_unique_dim0, x_unique)
            self.assertEqual(expected_inverse_dim0, x_inverse)
            self.assertEqual(expected_counts_dim0, x_counts)

            # dim1
            x_unique = torch.unique(x, dim=1)
            if x.dtype == torch.bool:
                self.assertEqual(expected_unique_dim1_bool, x_unique)
            else:
                self.assertEqual(expected_unique_dim1, x_unique)

            x_unique, x_inverse = torch.unique(x, return_inverse=True, dim=1)
            if x.dtype == torch.bool:
                self.assertEqual(expected_unique_dim1_bool, x_unique)
                self.assertEqual(expected_inverse_dim1_bool, x_inverse)
            else:
                self.assertEqual(expected_unique_dim1, x_unique)
                self.assertEqual(expected_inverse_dim1, x_inverse)

            x_unique, x_counts = torch.unique(
                x, return_inverse=False, return_counts=True, dim=1
            )
            if x.dtype == torch.bool:
                self.assertEqual(expected_unique_dim1_bool, x_unique)
                self.assertEqual(expected_counts_dim1_bool, x_counts)
            else:
                self.assertEqual(expected_unique_dim1, x_unique)
                self.assertEqual(expected_counts_dim1, x_counts)

            x_unique, x_inverse, x_counts = torch.unique(
                x, return_inverse=True, return_counts=True, dim=1
            )
            if x.dtype == torch.bool:
                self.assertEqual(expected_unique_dim1_bool, x_unique)
                self.assertEqual(expected_inverse_dim1_bool, x_inverse)
                self.assertEqual(expected_counts_dim1_bool, x_counts)
            else:
                self.assertEqual(expected_unique_dim1, x_unique)
                self.assertEqual(expected_inverse_dim1, x_inverse)
                self.assertEqual(expected_counts_dim1, x_counts)

            # dim2
            x_unique = torch.unique(x, dim=2)
            self.assertEqual(expected_unique_dim2, x_unique)

            x_unique, x_inverse = torch.unique(x, return_inverse=True, dim=2)
            self.assertEqual(expected_unique_dim2, x_unique)
            self.assertEqual(expected_inverse_dim2, x_inverse)

            x_unique, x_counts = torch.unique(
                x, return_inverse=False, return_counts=True, dim=2
            )
            self.assertEqual(expected_unique_dim2, x_unique)
            self.assertEqual(expected_counts_dim2, x_counts)

            x_unique, x_inverse, x_counts = torch.unique(
                x, return_inverse=True, return_counts=True, dim=2
            )
            self.assertEqual(expected_unique_dim2, x_unique)
            self.assertEqual(expected_inverse_dim2, x_inverse)
            self.assertEqual(expected_counts_dim2, x_counts)

            # test empty tensor
            x_unique, x_inverse, x_counts = torch.unique(
                x_empty, return_inverse=True, return_counts=True, dim=1
            )
            self.assertEqual(expected_unique_empty, x_unique)
            self.assertEqual(expected_inverse_empty, x_inverse)
            self.assertEqual(expected_counts_empty, x_counts)

            # test tensor with nan
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                x_unique, x_inverse, x_counts = torch.unique(
                    x_nan, return_inverse=True, return_counts=True, dim=0
                )
                self.assertEqual(expected_unique_nan, x_unique)
                self.assertEqual(expected_inverse_nan, x_inverse)
                self.assertEqual(expected_counts_nan, x_counts)

            # test not a well formed tensor
            # Checking for runtime error, as this is the expected behaviour
            with self.assertRaises(RuntimeError):
                torch.unique(
                    x_ill_formed_empty, return_inverse=True, return_counts=True, dim=1
                )

            # test along dim2
            with self.assertRaises(RuntimeError):
                torch.unique(
                    x_ill_formed_empty_another,
                    return_inverse=True,
                    return_counts=True,
                    dim=2,
                )

            # test consecutive version
            y = torch.tensor(
                [
                    [0, 1],
                    [0, 1],
                    [0, 1],
                    [1, 2],
                    [1, 2],
                    [3, 4],
                    [0, 1],
                    [0, 1],
                    [3, 4],
                    [1, 2],
                ],
                dtype=dtype,
                device=device,
            )
            # test tensor with nan
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                y_nan = torch.tensor(
                    [float("nan"), 0, 0, float("nan"), float("nan"), 1],
                    dtype=dtype,
                    device=device,
                )

            expected_y_unique = torch.tensor(  # noqa: F841
                [[0, 1], [1, 2], [3, 4], [0, 1], [3, 4], [1, 2]],
                dtype=dtype,
                device=device,
            )
            expected_y_inverse = torch.tensor(
                [0, 0, 0, 1, 1, 2, 3, 3, 4, 5], dtype=torch.int64, device=device
            )
            expected_y_counts = torch.tensor(
                [3, 2, 1, 2, 1, 1], dtype=torch.int64, device=device
            )
            expected_y_inverse_bool = torch.tensor(
                [0, 0, 0, 1, 1, 1, 2, 2, 3, 3], dtype=torch.int64, device=device
            )
            expected_y_counts_bool = torch.tensor(
                [3, 3, 2, 2], dtype=torch.int64, device=device
            )
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                expected_y_unique_nan = torch.tensor(
                    [float("nan"), 0, float("nan"), float("nan"), 1],
                    dtype=dtype,
                    device=device,
                )
                expected_y_inverse_nan = torch.tensor(
                    [0, 1, 1, 2, 3, 4], dtype=torch.long, device=device
                )
                expected_y_counts_nan = torch.tensor(
                    [1, 2, 1, 1, 1], dtype=torch.long, device=device
                )

            y_unique, y_inverse, y_counts = torch.unique_consecutive(
                y, return_inverse=True, return_counts=True, dim=0
            )
            if x.dtype == torch.bool:
                self.assertEqual(expected_y_inverse_bool, y_inverse)
                self.assertEqual(expected_y_counts_bool, y_counts)
            else:
                self.assertEqual(expected_y_inverse, y_inverse)
                self.assertEqual(expected_y_counts, y_counts)

            # test tensor with nan
            if dtype in floating_types_and(torch.float16, torch.bfloat16):
                y_unique, y_inverse, y_counts = torch.unique_consecutive(
                    y_nan, return_inverse=True, return_counts=True, dim=0
                )
                self.assertEqual(expected_y_unique_nan, y_unique)
                self.assertEqual(expected_y_inverse_nan, y_inverse)
                self.assertEqual(expected_y_counts_nan, y_counts)

            # Test dim is sorted same as NumPy with dims >= 3
            x = torch.tensor(
                [
                    [
                        [[1, 0, 1, 0, 1, 1], [0, 1, 1, 0, 1, 1]],
                        [[0, 1, 1, 0, 0, 1], [0, 0, 0, 1, 0, 0]],
                    ],
                    [
                        [[0, 1, 0, 1, 1, 1], [0, 1, 1, 0, 1, 1]],
                        [[0, 0, 1, 1, 0, 1], [1, 1, 0, 0, 0, 0]],
                    ],
                ],
                dtype=dtype,
                device=device,
            )
            xn = x.cpu().numpy()
            for d in range(x.dim()):
                t = torch.unique(x, dim=d)
                n = np.unique(xn, axis=d)
                self.assertEqual(t.cpu().numpy(), n)
def test_construction_from_list(self, device, dtype):
        from torch.fx.experimental.symbolic_shapes import is_nested_int

        # success case: single ragged dim anywhere but the batch dim
        for nt_dim in [2, 3, 4]:
            for ragged_dim in range(1, nt_dim):
                B = 6
                shapes = [list(range(3, 3 + nt_dim - 1)) for _ in range(B)]
                for b in range(B):
                    # subtract 1 to convert to component dim space
                    shapes[b][ragged_dim - 1] = torch.randint(
                        2, 9, (1,), device=device, dtype=torch.int64
                    ).item()

                components = [
                    torch.randn(shape, device=device, dtype=dtype) for shape in shapes
                ]
                nt = torch.nested.nested_tensor(components, layout=torch.jagged)

                self.assertEqual(nt.dim(), nt_dim)
                self.assertEqual(nt._ragged_idx, ragged_dim)
                for d in range(nt_dim):
                    self.assertEqual(d == ragged_dim, is_nested_int(nt.shape[d]))

        # error case: empty list
        with self.assertRaisesRegex(
            RuntimeError, "Cannot construct a nested tensor from an empty tensor list"
        ):
            torch.nested.nested_tensor([], layout=torch.jagged)

        # error case: list of zero-dim tensors
        with self.assertRaisesRegex(
            RuntimeError,
            "Cannot construct a nested tensor from a list of zero-dim tensors",
        ):
            torch.nested.nested_tensor(
                [
                    torch.tensor(3.0, device=device, dtype=dtype),
                    torch.tensor(4.0, device=device, dtype=dtype),
                    torch.tensor(5.0, device=device, dtype=dtype),
                ],
                layout=torch.jagged,
            )

        # error case: multiple ragged dims
        with self.assertRaisesRegex(
            RuntimeError,
            "Cannot represent given tensor list as a nested tensor with the jagged layout",
        ):
            torch.nested.nested_tensor(
                [
                    torch.randn(2, 3, device=device, dtype=dtype),
                    torch.randn(4, 5, device=device, dtype=dtype),
                ],
                layout=torch.jagged,
            )

        # error case: components on multiple devices
        if "cuda" in device:
            with self.assertRaisesRegex(
                RuntimeError,
                "When constructing a nested tensor, all tensors in list must be on the same device",
            ):
                torch.nested.nested_tensor(
                    [
                        torch.randn(2, 3, device=device, dtype=dtype),
                        torch.randn(2, 4, device="cpu", dtype=dtype),
                    ],
                    layout=torch.jagged,
                )

        # error case: components with multiple dtypes
        with self.assertRaisesRegex(
            RuntimeError,
            "When constructing a nested tensor, all tensors in list must have the same dtype",
        ):
            torch.nested.nested_tensor(
                [
                    torch.randn(2, 3, device=device, dtype=dtype),
                    torch.randn(2, 4, device=device, dtype=torch.float64),
                ],
                layout=torch.jagged,
            )

        # error case: components with multiple dims
        with self.assertRaisesRegex(
            RuntimeError,
            "When constructing a nested tensor, all tensors in list must have the same dim",
        ):
            torch.nested.nested_tensor(
                [
                    torch.randn(2, 3, device=device, dtype=dtype),
                    torch.randn(2, 3, 4, device=device, dtype=dtype),
                ],
                layout=torch.jagged,
            )
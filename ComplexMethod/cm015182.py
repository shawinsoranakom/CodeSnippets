def test_view_dtype_new(self, device, dtype):
        dtypes = {value: key for (key, value) in numpy_to_torch_dtype_dict.items()}
        if device.startswith("mps"):
            del dtypes[torch.float64]
        del dtypes[torch.bool]

        def generate_inputs():
            yield make_tensor((4, 4, 64), dtype=dtype, device=device, low=-5, high=5)
            yield make_tensor(
                (4, 4, 64), dtype=dtype, device=device, low=-5, high=5
            ).permute(1, 0, 2)
            yield make_tensor(
                (4, 64, 4), dtype=dtype, device=device, low=-5, high=5
            ).permute(2, 0, 1)
            yield make_tensor(
                (1, 5, 1), dtype=dtype, device=device, low=-5, high=5
            ).expand(5, 5, 64)
            yield make_tensor((2, 5, 256), dtype=dtype, device=device, low=-5, high=5)[
                1::2, 1:, ::2
            ]
            yield make_tensor((0, 5, 64), dtype=dtype, device=device, low=-5, high=5)
            yield make_tensor((), dtype=dtype, device=device, low=-5, high=5)

        def calc_expected_size_and_stride(a, view_dtype):
            dtype_size = torch._utils._element_size(a.dtype)
            view_dtype_size = torch._utils._element_size(view_dtype)

            if dtype_size == view_dtype_size:
                return a.size(), a.stride()

            elif dtype_size > view_dtype_size:
                size_ratio = dtype_size // view_dtype_size

                view_size = list(a.size())
                view_size[-1] = view_size[-1] * size_ratio

                view_stride = [stride * size_ratio for stride in a.stride()]
                view_stride[-1] = 1
                return torch.Size(view_size), tuple(view_stride)

            else:
                size_ratio = view_dtype_size // dtype_size

                view_size = list(a.size())
                view_size[-1] = view_size[-1] // size_ratio

                view_stride = [stride // size_ratio for stride in a.stride()]
                view_stride[-1] = 1
                return torch.Size(view_size), tuple(view_stride)

        for a in generate_inputs():
            a_np = a.cpu().numpy()
            a_np_contiguous = a.cpu().contiguous().numpy()

            for view_dtype, np_view_dtype in dtypes.items():
                equal_element_size = torch._utils._element_size(
                    dtype
                ) == torch._utils._element_size(view_dtype)

                if not equal_element_size and a.dim() == 0:
                    with self.assertRaisesRegex(
                        RuntimeError, r"self.dim\(\) cannot be 0"
                    ):
                        a.view(view_dtype)
                    continue

                if not equal_element_size and a.stride(-1) != 1:
                    with self.assertRaisesRegex(
                        RuntimeError, r"self.stride\(-1\) must be 1"
                    ):
                        a.view(view_dtype)
                    continue

                a_view = a.view(view_dtype)
                self.assertEqual(a_view.dtype, view_dtype)
                self.assertEqual(a.data_ptr(), a_view.data_ptr())

                expected_size, expected_stride = calc_expected_size_and_stride(
                    a, view_dtype
                )
                self.assertEqual(a_view.size(), expected_size)
                self.assertEqual(a_view.stride(), expected_stride)

                self.assertEqual(a_view.view(dtype), a, rtol=0, atol=0)

                # NumPy's dtype view requires contiguous input if target
                # dtype is a different size
                if equal_element_size:
                    a_np_view = a_np.view(np_view_dtype)

                else:
                    a_np_view = a_np_contiguous.view(np_view_dtype)

                self.assertEqual(a_view, a_np_view)

        # Test that requires_grad is dropped for floating point casts,
        # because view(dtype) does not support backward yet
        # TODO: Remove this when autograd support is added
        if dtype.is_floating_point or dtype.is_complex:
            for view_dtype in floating_and_complex_types_and(
                torch.half, torch.bfloat16
            ):
                t = make_tensor(
                    (5, 5, 64),
                    dtype=dtype,
                    device=device,
                    low=-5,
                    high=5,
                    requires_grad=True,
                )
                self.assertFalse(t.view(view_dtype).requires_grad)
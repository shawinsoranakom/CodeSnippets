def test_vector_norm(self, device, dtype):
        if IS_ARM64 and device == 'cpu' and dtype in [torch.float16, torch.bfloat16, torch.float32]:
            raise unittest.SkipTest("Fails on ARM, see https://github.com/pytorch/pytorch/issues/125438")
        # have to use torch.randn(...).to(bfloat16) instead of
        # This test compares torch.linalg.vector_norm's output with
        # torch.linalg.norm given a flattened tensor
        ord_vector = [0, 0.9, 1, 2, 3, inf, -0.5, -1, -2, -3, -inf, 1 + 2j]
        input_sizes = [
            (1, ),
            (10, ),
            (4, 5),
            (3, 4, 5),
            (0, ),
            (0, 10),
            (0, 0),
            (10, 0, 10),
        ]

        def vector_norm_reference(input, ord, dim=None, keepdim=False, dtype=None):
            if dim is None:
                input_maybe_flat = input.flatten(0, -1)
            else:
                input_maybe_flat = input

            result = torch.linalg.norm(input_maybe_flat, ord, dim=dim, keepdim=keepdim, dtype=dtype)
            if keepdim and dim is None:
                result = result.reshape([1] * input.dim())
            return result

        def run_test_case(input, ord, dim, keepdim, norm_dtype):
            if isinstance(ord, complex):
                error_msg = "Expected a non-complex scalar"
                with self.assertRaisesRegex(RuntimeError, error_msg):
                    torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
            elif (input.numel() == 0 and
                  (ord < 0. or ord == inf) and
                  (dim is None or input.shape[dim] == 0)):
                # The operation does not have an identity.
                error_msg = "linalg.vector_norm cannot compute"
                with self.assertRaisesRegex(RuntimeError, error_msg):
                    torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim)
            else:
                msg = (f'input.size()={input.size()}, ord={ord}, dim={dim}, '
                       f'keepdim={keepdim}, dtype={dtype}, norm_dtype={norm_dtype}')
                result_dtype_reference = vector_norm_reference(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                result_dtype = torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                if dtype.is_complex:
                    result_dtype_reference = result_dtype_reference.real
                self.assertEqual(result_dtype, result_dtype_reference, msg=msg)

                if norm_dtype is not None:
                    ref = torch.linalg.vector_norm(input.to(norm_dtype), ord, dim=dim, keepdim=keepdim)
                    actual = torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                    self.assertEqual(ref, actual, msg=msg)

        if dtype == torch.cfloat:
            norm_dtypes = (None, torch.cfloat, torch.cdouble)
        elif dtype == torch.cdouble:
            norm_dtypes = (None, torch.cdouble)
        elif dtype in (torch.float16, torch.bfloat16, torch.float):
            norm_dtypes = (None, torch.float, torch.double)
        elif dtype == torch.double:
            norm_dtypes = (None, torch.double)
        else:
            raise RuntimeError("Unsupported dtype")

        for amp in [False, True]:
            with torch.autocast(device_type=device, enabled=amp):
                for input_size, ord, keepdim, norm_dtype in product(input_sizes, ord_vector, [True, False], norm_dtypes):
                    input = make_tensor(input_size, dtype=dtype, device=device, low=-9, high=9)
                    for dim in [None, random.randint(0, len(input_size) - 1)]:
                        run_test_case(
                            input,
                            ord,
                            dim,
                            keepdim,
                            norm_dtype)
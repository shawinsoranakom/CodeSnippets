def test__int_mm(self, device, k, n, use_transpose_a, use_transpose_b):
        # Skip specific failing cases on CUDA 13.0
        if (not TEST_WITH_ROCM) and _get_torch_cuda_version() >= (13, 0):
            if not use_transpose_a and not use_transpose_b:
                self.skipTest("xfail on CUDA 13 until cuBLAS adds the supported kernel")

        def genf_int_float(x, y, use_transpose):
            if use_transpose:
                x, y = y, x
            x_int8 = torch.randint(-10, 10, (x, y), dtype=torch.int8, device=device)
            x_float = x_int8.to(torch.float32)
            if use_transpose:
                return x_int8.t(), x_float.t()
            return x_int8, x_float

        def _test(m, k, n, transpose_a, transpose_b, test_equal=True):
            a_int8, a_float = genf_int_float(m, k, transpose_a)
            b_int8, b_float = genf_int_float(k, n, transpose_b)
            c_int32 = torch._int_mm(a_int8, b_int8)
            self.assertTrue(c_int32.dtype is torch.int32)
            self.assertEqual(c_int32.device, torch.device(device))
            if test_equal:
                self.assertEqual(c_int32.float(), torch.mm(a_float, b_float))
            else:
                self.assertNotEqual(c_int32.float(), torch.mm(a_float, b_float))
            c_int32_result = c_int32.new_empty(c_int32.size())
            # Checking out variant
            torch._int_mm(a_int8, b_int8, out=c_int32_result)
            if test_equal:
                self.assertEqual(c_int32_result.float(), torch.mm(a_float, b_float))
            else:
                self.assertNotEqual(c_int32_result.float(), torch.mm(a_float, b_float))

        # NOTE: We're just exercising terrible failures here.
        version = _get_torch_cuda_version()
        SM80OrLater = torch.cuda.is_available() and torch.cuda.get_device_capability() >= (8, 0)
        SM70 = torch.cuda.is_available() and torch.cuda.get_device_capability() == (7, 0)
        SM75 = torch.cuda.is_available() and torch.cuda.get_device_capability() == (7, 5)

        if TEST_WITH_ROCM:
            _test(17, k, n, use_transpose_a, use_transpose_b, True)
        else:
            if not use_transpose_a and use_transpose_b:
                if SM80OrLater or (version >= (12, 3) and (SM70 or SM75)):
                    _test(17, k, n, use_transpose_a, use_transpose_b, version > (11, 7))
                else:
                    with self.assertRaisesRegex(RuntimeError,
                                                "CUDA error: CUBLAS_STATUS_NOT_SUPPORTED when calling cublasLtMatmul"):
                        _test(17, k, n, use_transpose_a, use_transpose_b)

            if use_transpose_a and not use_transpose_b:
                with self.assertRaisesRegex(RuntimeError,
                                            "CUDA error: CUBLAS_STATUS_NOT_SUPPORTED when calling cublasLtMatmul"):
                    _test(17, k, n, use_transpose_a, use_transpose_b)

            if use_transpose_a and use_transpose_b:
                with self.assertRaisesRegex(RuntimeError,
                                            "CUDA error: CUBLAS_STATUS_NOT_SUPPORTED when calling cublasLtMatmul"):
                    _test(17, k, n, use_transpose_a, use_transpose_b)

            if not use_transpose_a and not use_transpose_b:
                if SM80OrLater or (version >= (12, 3) and (SM70 or SM75)):
                    _test(17, k, n, use_transpose_a, use_transpose_b)
                else:
                    with self.assertRaisesRegex(RuntimeError,
                                                "CUDA error: CUBLAS_STATUS_NOT_SUPPORTED when calling cublasLtMatmul"):
                        _test(17, k, n, use_transpose_a, use_transpose_b)
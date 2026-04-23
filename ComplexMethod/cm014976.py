def test_sparse_semi_structured_ops_cutlass(self, device, dtype, backend):
        SparseSemiStructuredTensor._FORCE_CUTLASS = backend == "cutlass"
        if backend == "cutlass" and IS_WINDOWS:
            self.skipTest("CUTLASS not supported on Windows")

        def run_test(m, n, k, device, dtype, dtype_out, use_input, rtol, atol):
            mat1 = rand_sparse_semi_structured(m, k, dtype, device)
            # mat2 transposed as int8 case supports only row-major/column-major combination
            mat2 = make_tensor((n, k), dtype=dtype, device=device).t()
            input = (
                make_tensor((m,), dtype=dtype_out, device=device) if use_input else None
            )

            if use_input:
                if dtype.is_floating_point:
                    alpha = 1.3
                    beta = -0.7
                else:
                    alpha = 2
                    beta = -3

            dtype_dense = torch.float32
            mat1_dense = mat1.to(dtype_dense)
            mat2_dense = mat2.to(dtype_dense)
            if not use_input:
                output0 = torch.mm(mat1_dense, mat2_dense)
            else:
                input_dense = input.to(dtype_dense)[:, None]
                output0 = torch.addmm(
                    input_dense, mat1_dense, mat2_dense, alpha=alpha, beta=beta
                )

            compressed = to_sparse_semi_structured(mat1)

            mat1_sparse = compressed.values()
            mat1_meta = compressed.indices()

            if not use_input:
                output1 = torch._sparse_semi_structured_mm(
                    mat1_sparse, mat1_meta, mat2, out_dtype=dtype_out
                )
            else:
                output1 = torch._sparse_semi_structured_addmm(
                    input,
                    mat1_sparse,
                    mat1_meta,
                    mat2,
                    alpha=alpha,
                    beta=beta,
                    out_dtype=dtype_out,
                )
            torch.testing.assert_close(
                output1.to(dtype_dense), output0, rtol=rtol, atol=atol
            )

        if dtype == torch.float32:
            # Inputs are converted to TF32 internally for sparse GEMM,
            # so make dense GEMM to do the same for matching results.
            orig = torch.backends.cuda.matmul.allow_tf32
            torch.backends.cuda.matmul.allow_tf32 = True

        dtype_out = {
            torch.int8: torch.int32,
            torch.half: torch.half,
            torch.bfloat16: torch.bfloat16,
            torch.float32: torch.float32,
        }
        rtol, atol = 1e-3, 1e-3
        if dtype == torch.bfloat16:
            rtol, atol = 5e-3, 5e-3
        elif dtype == torch.float32:
            rtol, atol = 1e-3, 75e-2
        for m, n, k, use_input in itertools.product(
            range(3), range(3), range(3), (False, True)
        ):
            m = 2**m * 32
            n = 2**n * 32
            k = 2**k * 128
            run_test(m, n, k, device, dtype, dtype_out[dtype], use_input, rtol, atol)

        if dtype == torch.float32:
            torch.backends.cuda.matmul.allow_tf32 = orig
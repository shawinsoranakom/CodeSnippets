def test_linear_cutlass(self, device, dtype):
        def run_test(
            batch_shape,
            m,
            n,
            k,
            device,
            dtype,
            dtype_out,
            add_bias,
            activation,
            rtol,
            atol,
        ):
            weight = rand_sparse_semi_structured(m, k, dtype, device)
            input = make_tensor((*batch_shape, n, k), dtype=dtype, device=device)
            bias = (
                make_tensor((m,), dtype=dtype_out, device=device) if add_bias else None
            )

            dtype_dense = torch.float32
            input_dense = input.to(dtype_dense)
            weight_dense = weight.to(dtype_dense)
            bias_dense = bias.to(dtype_dense) if add_bias else None
            output0 = torch.nn.functional.linear(
                input_dense, weight_dense, bias=bias_dense
            )
            if activation == "relu":
                relu = torch.nn.ReLU()
                output0 = relu(output0)
            elif activation == "silu":
                silu = torch.nn.SiLU()
                output0 = silu(output0)

            compressed = to_sparse_semi_structured(weight)

            weight_sparse = compressed.values()
            meta = compressed.indices()

            output1 = torch._sparse_semi_structured_linear(
                input,
                weight_sparse,
                meta,
                bias=bias,
                activation=activation,
                out_dtype=dtype_out if dtype == torch.int8 else None,
            )
            torch.testing.assert_close(
                output1.to(dtype_dense), output0, rtol=rtol, atol=atol
            )

        if dtype == torch.float32:
            # Inputs are converted to TF32 internally for sparse GEMM,
            # so make dense GEMM to do the same for matching results.
            orig = torch.backends.cuda.matmul.allow_tf32
            torch.backends.cuda.matmul.allow_tf32 = True

        batch_shapes = [[], [3], [3, 1]]
        dtype_out = {
            torch.int8: torch.int32,
            torch.half: torch.half,
            torch.bfloat16: torch.bfloat16,
            torch.float32: torch.float32,
        }
        activations = [None, "relu", "silu"]
        rtol, atol = 1e-3, 1e-3
        if dtype == torch.bfloat16:
            rtol, atol = 5e-3, 5e-3
        elif dtype == torch.float32:
            rtol, atol = 1e-3, 75e-2
        for batch_shape, m, n, k, add_bias, activation in itertools.product(
            batch_shapes, range(3), range(3), range(3), (False, True), activations
        ):
            if activation == "silu" and dtype == torch.int8:
                continue  # SiLU not supported for integer inputs

            m = 2**m * 32
            n = 2**n * 32
            k = 2**k * 128
            run_test(
                batch_shape,
                m,
                n,
                k,
                device,
                dtype,
                dtype_out[dtype],
                add_bias,
                activation,
                rtol,
                atol,
            )

        if dtype == torch.float32:
            torch.backends.cuda.matmul.allow_tf32 = orig
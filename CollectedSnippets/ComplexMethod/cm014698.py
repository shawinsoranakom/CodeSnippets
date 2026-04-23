def run_test(
            batch_shape,
            m,
            n,
            k,
            add_bias,
            activation,
            dtype,
            dtypeq,
            device,
            rtol,
            atol,
        ):
            if not add_bias and activation != "none":
                return

            val_lo, val_hi = -1, 1
            valq_lo, valq_hi = -2, 2
            input = make_tensor(
                *batch_shape, m, k, low=val_lo, high=val_hi, dtype=dtype, device=device
            )
            weight = make_tensor(
                n, k, low=valq_lo, high=valq_hi, dtype=torch.int8, device=device
            )
            scale = make_tensor(
                (n,), low=val_lo, high=val_hi, dtype=input.dtype, device=device
            )
            bias = (
                make_tensor(
                    (n,), low=val_lo, high=val_hi, dtype=input.dtype, device=device
                )
                if add_bias
                else None
            )

            input_ref = input.reshape(-1, input.shape[-1])

            # First, test plain multiplication.
            weight_ref = weight.T.to(torch.float32) * scale.float().view(1, n)
            weightq = (
                pack_int4_to_int8(weight.T) if dtypeq == torch.quint4x2 else weight.T
            )
            output_ref = torch.mm(input_ref.float(), weight_ref).to(input.dtype).reshape(*input.shape[:-1], n)
            output = torch.ops.aten._mixed_dtypes_linear(
                input,
                quantized_weight_reorder_for_mixed_dtypes_linear_cutlass(
                    weightq, dtypeq, transpose=False
                ),
                scale,
            )
            torch.testing.assert_close(output, output_ref, rtol=rtol, atol=atol)

            # Second, test the linear operator itself.
            weight_ref = weight.to(torch.float32) * scale.float().view(n, 1)
            weightq = pack_int4_to_int8(weight) if dtypeq == torch.quint4x2 else weight
            bias_ref = bias.float().view(1, n) if add_bias else None
            output_ref = torch.nn.functional.linear(
                input_ref.float(), weight_ref, bias=bias_ref
            ).to(input.dtype).reshape(*input.shape[:-1], n)
            if activation == "relu":
                relu = torch.nn.ReLU()
                output_ref = relu(output_ref)
            elif activation == "silu":
                silu = torch.nn.SiLU()
                output_ref = silu(output_ref)
            output = torch.ops.aten._mixed_dtypes_linear(
                input,
                quantized_weight_reorder_for_mixed_dtypes_linear_cutlass(
                    weightq, dtypeq, transpose=True
                ),
                scale,
                bias=bias,
                activation=activation,
            )
            torch.testing.assert_close(output, output_ref, rtol=rtol, atol=atol)
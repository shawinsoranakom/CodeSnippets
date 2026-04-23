def test_to_padded_tensor_compile(self, device, dtype, nt_dim, requires_grad):
        if dtype is torch.bool and requires_grad:
            # grads not supported for bool
            return

        if nt_dim == 2:
            post_seq_len_shape = ()
        elif nt_dim == 3:
            post_seq_len_shape = (10,)
        elif nt_dim == 4:
            post_seq_len_shape = (9, 10)

        nt = torch.nested.nested_tensor(
            [
                (
                    torch.randint(
                        2, (n, *post_seq_len_shape), device=device, dtype=dtype
                    )
                    if dtype is torch.bool
                    else torch.randn(n, *post_seq_len_shape, device=device, dtype=dtype)
                )
                for n in range(2, 9)
            ],
            layout=torch.jagged,
            requires_grad=requires_grad,
        )

        def f(x):
            return x.sin() + 1

        from torch.nested._internal.nested_tensor import nested_from_padded

        @torch.compile(fullgraph=True)
        def g(nt):
            def _g(nt):
                PADDING_VAL = 4.2
                padded = nt.to_padded_tensor(PADDING_VAL)
                padded = f(padded)
                # NB: sum_S must be specified to use the lowering for dense -> jagged
                # and get full fusion
                return nested_from_padded(
                    padded, nt.offsets(), sum_S=nt.values().shape[0]
                )

            # NB: use checkpointing to force fusion
            return torch.utils.checkpoint.checkpoint(_g, nt, use_reentrant=False)

        expected_output = f(nt)
        if requires_grad:
            expected_output.backward(torch.ones_like(expected_output))
            expected_grad = nt.grad.detach().clone()
            nt.grad = None

        from torch._inductor.utils import run_and_get_code

        compiled_output, generated_code = run_and_get_code(g, nt)
        if requires_grad:
            compiled_output.backward(torch.ones_like(compiled_output))
            compiled_grad = nt.grad.detach().clone()
            self.assertEqual(compiled_grad, expected_grad, rtol=1e-3, atol=1e-3)

        self.assertEqual(compiled_output, expected_output, rtol=1e-3, atol=1e-3)

        # === Verify that computation fusion happens. ===
        # Fallback op call -> fusion didn't happen.
        fallback_op_calls_present = any(
            "torch.ops.aten._padded_dense_to_jagged_forward.default("
            in generated_code[i]
            or "torch.ops.aten._jagged_to_padded_dense_forward.default("
            in generated_code[i]
            for i in range(len(generated_code))
        )

        # NB: Fusion isn't supported on CPU.
        self.assertEqual("cuda" in device, not fallback_op_calls_present)

        for i in range(len(generated_code)):
            # Examine buffer construction lines in the generated code to determine
            # whether fusion occurred. If fusion happens, a 3D buffer with shape
            # (B, max_seqlen, D) should never be materialized.
            buffer_constructions = [
                line.strip()
                for line in generated_code[i].split("\n")
                if "empty_strided_cuda(" in line
            ]

            buffer_dims = [
                # buffer dim == number of elements in the tensor size tuple arg
                len(ast.parse(t).body[0].value.args[0].elts)
                for t in buffer_constructions
            ]

            if "cuda" in device:
                self.assertFalse(any(d == 3 for d in buffer_dims))
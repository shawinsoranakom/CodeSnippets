def test_pointwise_op_with_0d_tensor1(self, device, dtype):
        # Test that foreach_addcmul/addcdiv uses fast path when tensor1 is a list of 0D tensors
        # This is a regression test for the optimization that allows 0D tensors in tensor1
        # to use the fast CUDA kernel path instead of falling back to the slow path.
        N = 5
        # Create regular tensors for input and tensor2
        inputs = [make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)]
        tensor2s = [
            make_tensor((10, 10), dtype=dtype, device=device, low=0.1) for _ in range(N)
        ]
        # Create 0D tensors for tensor1 (scalar tensors)
        tensor1s_0d = [
            torch.tensor(float(i + 1), dtype=dtype, device=device) for i in range(N)
        ]

        alpha = 0.5

        # Test with 0D tensors in either tensor1 or tensor2 position
        # For addcmul (commutative), both orderings should use the fast path
        # For addcdiv (non-commutative), only 0D tensor1 uses the fast path
        for swap_args in [False, True]:
            if swap_args:
                # 0D tensors in tensor2 position
                t1_args, t2_args = tensor2s, tensor1s_0d
            else:
                # 0D tensors in tensor1 position
                t1_args, t2_args = tensor1s_0d, tensor2s

            # Test foreach_addcmul (commutative - both orderings use fast path)
            foreach_addcmul = ForeachFuncWrapper(torch._foreach_addcmul)
            actual_addcmul = foreach_addcmul(
                [inputs, t1_args, t2_args],
                is_cuda=True,
                expect_fastpath=True,
                value=alpha,
            )
            expected_addcmul = [
                torch.addcmul(inp, t1, t2, value=alpha)
                for inp, t1, t2 in zip(inputs, t1_args, t2_args)
            ]
            self.assertEqual(actual_addcmul, expected_addcmul)

            # Test foreach_addcdiv (non-commutative - only 0D tensor1 uses fast path)
            if not swap_args:
                foreach_addcdiv = ForeachFuncWrapper(torch._foreach_addcdiv)
                actual_addcdiv = foreach_addcdiv(
                    [inputs, t1_args, t2_args],
                    is_cuda=True,
                    expect_fastpath=True,
                    value=alpha,
                )
                expected_addcdiv = [
                    torch.addcdiv(inp, t1, t2, value=alpha)
                    for inp, t1, t2 in zip(inputs, t1_args, t2_args)
                ]
                self.assertEqual(actual_addcdiv, expected_addcdiv)

            # Test inplace variants
            inputs_copy = [t.clone() for t in inputs]
            foreach_addcmul_inplace = ForeachFuncWrapper(torch._foreach_addcmul_)
            foreach_addcmul_inplace(
                [inputs_copy, t1_args, t2_args],
                is_cuda=True,
                expect_fastpath=True,
                value=alpha,
            )
            self.assertEqual(inputs_copy, expected_addcmul)

            if not swap_args:
                inputs_copy = [t.clone() for t in inputs]
                foreach_addcdiv_inplace = ForeachFuncWrapper(torch._foreach_addcdiv_)
                foreach_addcdiv_inplace(
                    [inputs_copy, t1_args, t2_args],
                    is_cuda=True,
                    expect_fastpath=True,
                    value=alpha,
                )
                self.assertEqual(inputs_copy, expected_addcdiv)
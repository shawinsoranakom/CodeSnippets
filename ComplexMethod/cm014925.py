def _test_transform_bias_rescale_qkv_impl(
        self, device, dtype, use_nt, use_padding=False
    ):
        tests = [
            (64, 4, 16, 8),
            # dim_per_head = 12 does not divide evenly by CPU vectorization length of 8
            (24, 2, 4, 2),
            # Make sure CUDA can handle small input sizes
            (2, 2, 2, 2),
            # dim_per_head = 6 does not divide evenly by CUDA vectorization length of 4,
            # causes alignment issues
            (24, 4, 4, 2),
            (48, 4, 16, 8),
        ]
        for (embed_dim, num_heads, bs, sl) in tests:
            with self.subTest(embed_dim=embed_dim, num_heads=num_heads, bs=bs, sl=sl):
                torch.manual_seed(9343)
                dense_x = x = (
                    torch.randn(bs, sl, 3 * embed_dim, device=device, dtype=dtype) * 10
                )
                if use_padding:
                    x[0][-1] = torch.full(x[0][-1].shape, float("-Inf"))
                if use_nt:
                    xs = list(torch.unbind(x))
                    if use_padding:
                        xs[0] = xs[0][:-1]
                    x = torch.nested.nested_tensor(xs, device=device, dtype=dtype)
                qkv = torch.nn.Linear(embed_dim, 3 * embed_dim, device=device, dtype=dtype)

                # We have to use inference_mode here because q/k/v are
                # all views of the same Tensor, which autograd doesn't
                # like. This is fine because this function is only
                # exposed to Python for purposes of writing this test.
                with torch.inference_mode():
                    (q, k, v) = torch._transform_bias_rescale_qkv(
                        x, qkv.bias, num_heads=num_heads
                    )

                    def simple_transform_bias_rescale_qkv(qkv, bias):
                        (q, k, v) = torch.split(qkv, embed_dim, dim=-1)
                        (q_bias, k_bias, v_bias) = torch.split(bias, embed_dim, dim=-1)

                        def embiggen(x):
                            if not use_nt:
                                return x
                            b, t, d = x.size()
                            t = t + (8 - t % 8) % 8
                            newsize = (b, t, d)
                            new_x = torch.zeros(newsize, device=device, dtype=dtype)
                            new_x[:x.size()[0], :x.size()[1], :x.size()[2]] = x
                            return new_x
                        return tuple(
                            embiggen(x).reshape(
                                (bs, -1, num_heads, embed_dim // num_heads)
                            ).transpose(2, 1)
                            for x in (
                                (q + q_bias) / math.sqrt(embed_dim // num_heads),
                                (k + k_bias),
                                (v + v_bias),
                            )
                        )

                    correct_q, correct_k, correct_v = simple_transform_bias_rescale_qkv(
                        dense_x, qkv.bias
                    )
                    if use_nt and use_padding:
                        for t in (correct_q, correct_k, correct_v):
                            t[t == float("-Inf")] = 0

                self.assertEqual(q.size(), correct_q.size())
                torch.testing.assert_close(q, correct_q)
                torch.testing.assert_close(k, correct_k)
                torch.testing.assert_close(v, correct_v)
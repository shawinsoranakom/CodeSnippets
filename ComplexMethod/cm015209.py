def test_sdpa(self, device, backend):
        if device == "cpu":
            raise unittest.SkipTest("This test is only for CUDA for now")

        def T(*args):
            return torch.randn(*args, dtype=torch.float16, device=device)

        backend_ctx = sdpa_kernel([backend])
        with backend_ctx:
            for batching in [
                (True, True, True),
                (True, False, False),
                (False, True, True),
            ]:
                size = [8, 4, 128, 64]
                if batching[0]:
                    query = T(3, *size)
                else:
                    query = T(*size)
                if batching[1]:
                    key = T(3, *size)
                else:
                    key = T(*size)
                if batching[2]:
                    value = T(3, *size)
                else:
                    value = T(*size)
                in_dims = tuple(0 if b else None for b in batching)
                attention = F.scaled_dot_product_attention

                self._vmap_test(
                    attention,
                    (query, key, value),
                    in_dims=in_dims,
                )
                # Backwards test doesn't work yet
                # self._batched_grad_test(
                #     lambda query, key, value: F.scaled_dot_product_attention(
                #         query, key, value
                #     ),
                #     (query, key, value),
                # )

            B = 4
            query = torch.rand(4, 32, B, 8, 128, dtype=torch.float16, device=device)
            key = torch.rand(4, B, 32, 8, 128, dtype=torch.float16, device=device)
            value = torch.rand(4, 32, 8, 128, dtype=torch.float16, device=device)
            self._vmap_test(
                F.scaled_dot_product_attention,
                (query, key, value),
                in_dims=(2, 1, None),
            )
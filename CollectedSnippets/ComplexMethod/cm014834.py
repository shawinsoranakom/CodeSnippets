def test_fully_masked_out_rows(self, backend, device, seq_len, head_dim, dtype):
        def attention_inputs(seq_len, head_dim, device, dtype, mask_every_n_rows=4):
            query = torch.rand(1, 1, seq_len, head_dim, requires_grad=True, device=device, dtype=dtype)
            key = torch.rand(1, 1, seq_len, head_dim, requires_grad=True, device=device, dtype=dtype)
            value = torch.rand(1, 1, seq_len, head_dim, requires_grad=True, device=device, dtype=dtype)

            # Create a mask with deterministic row masking
            mask = torch.ones(1, 1, seq_len, seq_len, dtype=torch.bool, device=device)

            # Mask every nth row
            mask[0, 0, ::mask_every_n_rows, :] = False

            # Create a fixed pattern for element-wise masking
            element_mask = torch.zeros(seq_len, seq_len, dtype=torch.bool, device=device)
            element_mask[torch.arange(seq_len)[:, None] % 5 == torch.arange(seq_len) % 5] = True

            # Combine row masking and element-wise masking
            mask = mask & element_mask.unsqueeze(0).unsqueeze(0)

            return query, key, value, mask

        def compute_output_and_grads(query, key, value, mask, backend):
            with sdpa_kernel(backend):
                masked_out = scaled_dot_product_attention(query, key, value, attn_mask=mask)
                loss = masked_out.sum()
            grads = torch.autograd.grad(loss, [query, key, value])
            return masked_out, grads

        if backend == SDPBackend.FLASH_ATTENTION and "cuda" in str(device):
            unittest.skip("FlashAttention does not support masks on cuda")
            return
        if backend == SDPBackend.EFFICIENT_ATTENTION and "cpu" in str(device):
            unittest.skip("EfficientAttention does not support masks on cpu")
            return
        query, key, value, mask = attention_inputs(seq_len, head_dim, device, dtype)

        # Compute results for the tested backend
        backend_out, backend_grads = compute_output_and_grads(query, key, value, mask, backend)

        # Compute results for the Math backend
        math_out, math_grads = compute_output_and_grads(query, key, value, mask, SDPBackend.MATH)

        # Compare outputs
        torch.testing.assert_close(backend_out, math_out, atol=5e-3, rtol=0)
        self.assertFalse(backend_out.isnan().any())
        self.assertFalse(math_out.isnan().any())
        # Compare gradients
        for bg, mg in zip(backend_grads, math_grads):
            torch.testing.assert_close(bg, mg, atol=3e-3, rtol=0)
            self.assertFalse(bg.isnan().any())
            self.assertFalse(mg.isnan().any())

        # Check if masked rows are zero in output
        mask_sum = mask.sum(dim=-1, keepdim=True)
        masked_rows = (mask_sum == 0).expand_as(backend_out)
        self.assertTrue((mask_sum == 0).sum() > 0, "No fully masked out rows found")
        if not torch.all(backend_out[masked_rows] == 0):
            raise AssertionError(f"Non-zero values in fully masked rows for {backend=}")

        # Check if gradients for masked rows are zero
        grad_query = backend_grads[0]
        if not torch.all(grad_query[masked_rows] == 0):
            raise AssertionError(f"Non-zero gradients in fully masked rows for {backend=}")
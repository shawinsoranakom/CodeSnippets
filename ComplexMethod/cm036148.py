def test_few_valid_tokens_with_neginf(self):
        """Only a handful of tokens are finite per row (strict grammar)."""
        from vllm.v1.sample.ops.topk_topp_triton import apply_top_k_top_p_triton

        batch_size, vocab_size = 32, 128256
        logits = torch.full(
            (batch_size, vocab_size), float("-inf"), dtype=torch.float32
        )
        # Allow only 5 random tokens per row to be finite.
        for i in range(batch_size):
            indices = torch.randperm(vocab_size, generator=self.generator)[:5]
            logits[i, indices] = torch.randn(
                5, generator=self.generator, dtype=torch.float32
            )

        k = torch.full((batch_size,), 50, dtype=torch.int32)
        p = torch.full((batch_size,), 0.9, dtype=torch.float32)

        # top-k only (k=50 but only 5 finite → keep all 5)
        result = apply_top_k_top_p_triton(logits.clone(), k, None)
        assert not result.isnan().any()
        for i in range(batch_size):
            kept = (result[i] > float("-inf")).sum().item()
            assert kept == 5, f"Row {i}: expected 5 kept, got {kept}"

        # top-k with k < num_finite
        k_small = torch.full((batch_size,), 3, dtype=torch.int32)
        result = apply_top_k_top_p_triton(logits.clone(), k_small, None)
        assert not result.isnan().any()
        for i in range(batch_size):
            kept = (result[i] > float("-inf")).sum().item()
            assert kept <= 3, f"Row {i}: expected <=3 kept, got {kept}"

        # top-p only
        result = apply_top_k_top_p_triton(logits.clone(), None, p)
        assert not result.isnan().any()
        for i in range(batch_size):
            kept = (result[i] > float("-inf")).sum().item()
            assert kept > 0, f"Row {i}: no tokens kept"
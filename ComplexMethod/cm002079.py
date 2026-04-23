def test_attention_mask(
        self,
        cumulative_seqlens_q: list[int],
        cumulative_seqlens_k: list[int],
        sliding_window: int,  # the sliding window size, 1 means no sliding window
        str_expected_mask_lines: list[str],  # the attention mask, broken down by line as a string of 0s and 1s
    ) -> None:
        """Tests the correctness of the attention mask used in the continuous batching API."""
        # Build expected mask
        minus_inf = torch.finfo(torch.float32).min
        expected_mask = torch.empty((cumulative_seqlens_q[-1], cumulative_seqlens_k[-1]), dtype=torch.float32)
        for i, line in enumerate(str_expected_mask_lines):
            expected_mask[i, :] = torch.tensor([minus_inf if c == "0" else 0 for c in line])
        # Build actual mask
        actual_mask = torch.full_like(expected_mask, minus_inf)  # function modifies in place
        build_attention_mask(actual_mask, cumulative_seqlens_q, cumulative_seqlens_k, sliding_window)
        # Check that the actual mask matches the expected mask
        matches = (expected_mask == actual_mask).all()
        # If it doesn't match, print the masks in a readable form and fail the test
        if not matches:
            str_mask = [
                "".join("1" if x == 0 else "0" for x in token_attn_vector) for token_attn_vector in actual_mask
            ]
            str_mask = "\n".join(str_mask)
            str_expected_mask = "\n".join(str_expected_mask_lines)
            self.fail(
                f"Test failed for: {cumulative_seqlens_q = }, {cumulative_seqlens_k = }, {sliding_window = }\n"
                f"Expected mask:\n{str_expected_mask}\n"
                f"Actual mask:\n{str_mask}"
            )
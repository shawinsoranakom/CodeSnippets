def test_compute_probabilities(
        self, label_logprobs, apply_softmax, should_sum_to_one
    ):
        """Test probability computation for softmax and true probability modes."""
        serving = OpenAIServingGenerativeScoring.__new__(OpenAIServingGenerativeScoring)
        probs = serving._compute_probabilities(
            label_logprobs, apply_softmax=apply_softmax
        )

        # Verify sum behavior
        total = sum(probs.values())
        if should_sum_to_one:
            assert abs(total - 1.0) < 1e-6
        else:
            assert total < 1.0

        # Verify math
        if apply_softmax:
            max_lp = max(label_logprobs.values())
            exp_vals = {k: math.exp(v - max_lp) for k, v in label_logprobs.items()}
            sum_exp = sum(exp_vals.values())
            for tid, lp in label_logprobs.items():
                assert abs(probs[tid] - exp_vals[tid] / sum_exp) < 1e-9
        else:
            for tid, lp in label_logprobs.items():
                assert abs(probs[tid] - math.exp(lp)) < 1e-9
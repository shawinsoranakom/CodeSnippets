def _estimate_compile_threshold(
        model,
        batch_size = None,
        grad_accum = None,
        max_seq_length = None,
    ):
        """
        Estimate the minimum training steps needed for torch.compile to be beneficial.
        Returns the threshold with a 1.2x safety margin built in.

        Based on empirical benchmarks:
        - Larger models have lower breakeven (more time saved per step)
        - Warmup time scales with model size but speedup also increases

        Optional inputs (batch_size, grad_accum, max_seq_length) allow
        a coarse pre-run adjustment. These are intentionally conservative
        and avoid any runtime measurements.
        """
        # Get parameter count from inner model
        if hasattr(model, "__getitem__"):
            try:
                inner = model[0].auto_model
                params = sum(p.numel() for p in inner.parameters())
            except:
                params = 100_000_000  # Default to 100M if can't determine
        else:
            params = sum(p.numel() for p in model.parameters())

        model_type = None
        try:
            if "inner" in locals():
                model_type = getattr(getattr(inner, "config", None), "model_type", None)
        except Exception:
            model_type = None
        if isinstance(model_type, str):
            model_type = model_type.lower()

        params_m = params / 1e6

        # Empirical formula based on benchmarks with batch_size=2, grad_accum=4
        # Small models: high fixed overhead, lower speedup
        # Large models: warmup scales but speedup is significant
        if params_m < 50:
            estimated_warmup = 35 + params_m * 0.3
            base_speedup = 1.35
        elif params_m < 200:
            estimated_warmup = 12 + params_m * 0.03
            base_speedup = 1.75
        else:
            estimated_warmup = 15 + params_m * 0.04
            base_speedup = 1.60

        # Estimate time per step (ms) and time saved
        naive_ms = 50 + params_m * 1.0
        compiled_ms = naive_ms / base_speedup
        time_saved_per_step_s = (naive_ms - compiled_ms) / 1000

        if time_saved_per_step_s > 0:
            breakeven = estimated_warmup / time_saved_per_step_s
        else:
            breakeven = float("inf")

        # Return threshold with 1.2x safety margin
        threshold = breakeven * 1.2

        # Optional adjustment based on expected work per step.
        # This uses only pre-run information (batch size, grad accum, seq length).
        generic_scale = 1.0
        fast_scale = 1.0
        if (
            batch_size is not None
            or grad_accum is not None
            or max_seq_length is not None
        ):
            try:
                bs = int(batch_size) if batch_size is not None else 2
                ga = int(grad_accum) if grad_accum is not None else 4
                seq = int(max_seq_length) if max_seq_length is not None else 512
            except Exception:
                bs, ga, seq = 2, 4, 512

            bs = max(1, bs)
            ga = max(1, ga)
            # Guard against unbounded tokenizer.model_max_length
            seq = max(64, min(seq, 8192))

            ref_bs, ref_ga, ref_seq = 2, 4, 512

            # Generic path: lighter scaling, less conservative than params-only.
            ga_scale = (ref_ga / ga) ** 1.0
            bs_seq_scale = ((ref_bs * ref_seq) / (bs * seq)) ** 0.15
            generic_scale = 0.35 * ga_scale * bs_seq_scale
            generic_scale = max(0.05, min(generic_scale, 5.0))

            # Fast encoder path: stronger scaling based on observed behavior.
            fast_ga_scale = (ref_ga / ga) ** 1.5
            fast_bs_seq_scale = ((ref_bs * ref_seq) / (bs * seq)) ** 0.25
            fast_scale = 0.2 * fast_ga_scale * fast_bs_seq_scale
            fast_scale = max(0.05, min(fast_scale, 5.0))

        # Conservative safety factors: generic is less conservative than fast.
        generic_threshold = threshold * generic_scale * 1.25

        is_fast_type = (
            isinstance(model_type, str)
            and model_type in FastSentenceTransformer.ENCODER_MODEL_TYPES
        )
        if is_fast_type:
            fast_threshold = threshold * fast_scale * 1.5
            # Prefer the smaller (less conservative) of the two estimates.
            final_threshold = min(generic_threshold, fast_threshold)
        else:
            final_threshold = generic_threshold

        # Reduce mpnet overestimation slightly.
        if model_type == "mpnet":
            final_threshold *= 0.7

        # Lower bound to avoid compiling on extremely short runs.
        return int(max(20, final_threshold))
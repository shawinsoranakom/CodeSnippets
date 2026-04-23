def should_use_persistent_reduction(
        features: SIMDKernelFeatures, cooperative_reduction: bool
    ) -> bool:
        """
        Heuristic to decide if a persistent reduction should be used.
        """
        if not config.triton.persistent_reductions:
            return False
        threshold = {
            ReductionHint.INNER: 1024,
        }.get(features.get_reduction_hint(), 64)

        if features.get_reduction_hint() not in (
            ReductionHint.INNER,
            ReductionHint.OUTER_TINY,
        ):
            bounds = bound_sympy(features.reduction_numel)
            lower = bounds.lower
            upper = bounds.upper

            if not all(
                (
                    (isinstance(bound, int) or bound.is_constant())
                    and not torch.utils._sympy.numbers.is_infinite(bound)
                )
                for bound in (lower, upper)
            ):
                return False

            lower = next_power_of_2(int(lower))
            upper = next_power_of_2(int(upper))

            # If we are coalescing on xblock (not ReductionHint.INNER) and this is not a tiny kernel
            # (not ReductionHint.OUTER_TINY), do not use persistent reduction if it induces tile
            # quantization. Persistent reduction forces rblock == rnumel, if the bounds between lower
            # and upper are large, for the lower values we will be masking off large % of read/writes,
            # when we could expand the coalescing xblock instead.
            if lower != upper:
                return False

        if cooperative_reduction:
            # The RSPLIT of cooperative reductions means each thread block is operating on fewer elements
            # The default fallback will be used if optimizations hint is not provided. The default fallback
            # is >> 32.
            threshold *= 32 // min(
                V.graph.sizevars.optimization_hint(features.numel), 32
            )

        # If multi_kernel is enabled, we do more aggressive persistent reduction.
        # This may result in some persistent reductions slower than the
        # corresponding non-persistent reductions. MultiKernel will do benchmarking
        # to pick the faster one.
        if config.triton.multi_kernel:
            threshold *= 16

        return V.graph.sizevars.statically_known_leq(
            features.reduction_numel, threshold
        )
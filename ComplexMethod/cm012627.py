def get_reduction_hint(
        self, tiling_scores: dict[str, int] | None = None
    ) -> ReductionHint:
        reductions = self.reduction_nodes()
        if len(reductions) > 0:
            hints = [self.reduction_hint(n) for n in reductions]
            if hints.count(hints[0]) == len(hints):
                reduction_hint_val = hints[0]
            else:
                reduction_hint_val = ReductionHint.DEFAULT

            if (
                reduction_hint_val == ReductionHint.INNER
                and self.has_non_contiguous_pw_in_reduction_kernel()
            ):
                reduction_hint_val = ReductionHint.DEFAULT

            # Upgrade DEFAULT to INNER for inner reductions based on tiling scores
            if (
                reduction_hint_val == ReductionHint.DEFAULT
                and tiling_scores is not None
                and "x" in tiling_scores
                and "r0_" in tiling_scores
            ):
                # If reduction dimension has much better coalescing than non-reduction dimensions,
                # this is an inner reduction
                from ..codegen.triton import INNER_REDUCTION_RATIO_THRESHOLD

                r_coalesce_ratio = tiling_scores["r0_"] / max(tiling_scores["x"], 1)
                contiguous_red = r_coalesce_ratio >= INNER_REDUCTION_RATIO_THRESHOLD
                if contiguous_red:
                    reduction_hint_val = ReductionHint.INNER
        else:
            reduction_hint_val = ReductionHint.DEFAULT
        return reduction_hint_val
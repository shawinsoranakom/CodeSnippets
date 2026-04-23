def _multilayer_second_step_hint(
        split: _IntLike, numel_hint: int, reduction_hint: ReductionHint
    ) -> ReductionHint:
        if split == -1:
            return reduction_hint
        if split <= 512 and numel_hint <= 512 and reduction_hint == ReductionHint.OUTER:
            return ReductionHint.OUTER_TINY
        if (
            split <= 1024
            and numel_hint <= 256
            and reduction_hint == ReductionHint.OUTER
        ):
            return ReductionHint.OUTER_TINY

        return reduction_hint
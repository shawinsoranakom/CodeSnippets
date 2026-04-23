def _is_tma_compatible(
        sizes: Sequence[sympy.Expr],
        strides: Sequence[_IntLike],
        dtype: torch.dtype,
    ) -> bool:
        rank = len(sizes)
        itemsize = dtype.itemsize

        if rank < 1 or rank > 5:
            return False

        if dtype not in _TMA_SUPPORTED_DTYPES:
            return False

        if add_guards:
            sizes_i = V.graph.sizevars.guard_int_seq(sizes)
            strides_i = V.graph.sizevars.guard_int_seq(strides)
        else:
            sizes_i = [
                V.graph.sizevars.replace_backed_symbols_with_hints(s) for s in sizes
            ]
            strides_i = [
                V.graph.sizevars.replace_backed_symbols_with_hints(st) for st in strides
            ]

        # Find the single contiguous ("inner") dim
        inner = [
            i
            for i, st in enumerate(strides_i)
            if V.graph.sizevars.statically_known_equals(st, 1)
        ]
        if len(inner) != 1:
            return False
        inner_idx = inner[0]

        # All "outer" dims must have 16-byte aligned strides
        for i, st in enumerate(strides_i):
            if i == inner_idx:
                continue
            if not _aligned(st * itemsize):
                return False

        # Inner dim byte width must be a multiple of 16 B
        inner_dim = sizes_i[inner_idx]
        if not _aligned(inner_dim * itemsize):
            return False

        # 1-byte dtypes (FP8 etc.) need inner dim ≥ 32 for tensor core alignment
        if itemsize == 1 and not V.graph.sizevars.statically_known_geq(inner_dim, 32):
            return False

        return True
def create(  # type: ignore[override]
        cls,
        device: torch.device,
        dtype: torch.dtype,
        inner_fns: Sequence[Callable[..., Any]],
        ranges: list[Integer],
        reduction_ranges: list[Integer],
        reduction_type: ReductionType,
        reduction_hint: ReductionHint = ReductionHint.DEFAULT,
    ) -> Sequence[TensorBox]:
        assert reduction_type in ("welford_reduce", "welford_combine")
        assert not config.mtia.disable_welford_reduction, (
            "welford reduction usage is explicitly disabled, please check you config"
        )

        reduction_numel = V.graph.sizevars.simplify(sympy_product(reduction_ranges))

        def const(val: int) -> TensorBox:
            def inner_fn(idx: Sequence[Expr]) -> OpsValue:
                return ops.constant(
                    val,
                    dtype,
                )

            return Pointwise.create(
                device=device,
                dtype=dtype,
                inner_fn=inner_fn,
                ranges=list(ranges),
            )

        if reduction_numel == 0:
            mean = const(0)
            m2 = const(0)
            weight = const(0)
            return mean, m2, weight

        if reduction_numel == 1:

            def copy(
                loader: Callable[[Sequence[Expr], Sequence[Expr]], OpsValue],
            ) -> TensorBox:
                def inner_fn(idx: Sequence[Expr]) -> OpsValue:
                    reduction_index = [sympy.S.Zero for _ in reduction_ranges]
                    return loader(idx, reduction_index)

                return Pointwise.create(
                    device=device,
                    dtype=dtype,
                    inner_fn=inner_fn,
                    ranges=list(ranges),
                )

            if reduction_type == "welford_reduce":
                return copy(inner_fns[0]), const(0), const(1)
            else:
                return tuple(copy(fn) for fn in inner_fns)

        # TODO: Unrolled reduction
        # if (
        #     isinstance(reduction_numel, Integer)
        #     and int(reduction_numel)
        #     < config.unroll_reductions_threshold
        #     and sympy_product(ranges) != 1
        # ):
        #     return Pointwise.create(
        #         device,
        #         dst_dtype,
        #         cls._unroll_reduction_fn(
        #             inner_fn, reduction_ranges, reduction_type, src_dtype,
        #         ),
        #         ranges,
        #     )

        # triton doesn't support reduce to single element well, so break it up
        hint, split = Reduction.num_splits(
            device,
            dtype,
            dtype,
            inner_fns[0],
            ranges,
            reduction_ranges,
            reduction_type=reduction_type,
            reduction_numel=reduction_numel,
        )
        # intermediate reduction in split can contain complex indexing,
        # and num_splits will fail to correctly set the hint
        # reuse the passed hint if available
        if reduction_hint == ReductionHint.DEFAULT:
            reduction_hint = hint
        if split > 1:
            # triton doesn't support reduce to single element well, so break it up
            return cls.create_multilayer(
                device,
                dtype,
                inner_fns,
                ranges,
                reduction_ranges,
                reduction_type,
                split,
                reduction_hint,
            )

        results = [
            TensorBox.create(
                WelfordReduction(
                    device,
                    dtype,
                    inner_fns,
                    ranges,
                    reduction_ranges,
                    reduction_type,
                    dtype,
                    reduction_hint,
                    output_idx,
                )
            )
            for output_idx in range(3)
        ]
        for t in results:
            t.realize()
        return results
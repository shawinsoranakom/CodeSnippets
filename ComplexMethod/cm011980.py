def create(  # type: ignore[override]
        cls,
        device: torch.device,
        dtypes: tuple[torch.dtype, ...],
        inner_fns: tuple[Callable[[list[Expr]], Any], ...],
        size: list[Integer],
        axis: int,
        stable: bool,
        descending: bool,
        reduction_hint: ReductionHint = ReductionHint.DEFAULT,
        **kwargs: Any,
    ) -> Sequence[TensorBox | None]:
        pointwise_ranges = [*size[:axis], *size[axis + 1 :]]
        sort_ranges = [size[axis]]

        if not V.graph.has_feature(device, BackendFeature.SORT):
            return [None] * len(dtypes)

        sizevars = V.graph.sizevars
        sort_numel = sizevars.simplify(sympy_product(sort_ranges))

        # Heuristic, smallest rblock where triton usually outperforms aten.sort.
        # It also isn't bandwidth bound so fusion is unlikely to help.
        # When decompose_sort_ops is enabled, skip the size limit to always
        # attempt Triton sort (index dtype is widened to int32 in lowering).
        if config.triton.decompose_sort_ops:
            is_persistent_kernel = config.triton.persistent_reductions
        else:
            max_rblock = 512
            is_persistent_kernel = (
                config.triton.persistent_reductions
                and sizevars.statically_known_true(sympy.Le(sort_numel, max_rblock))
            )
        if not is_persistent_kernel:
            # We only support persistent triton kernels
            return [None] * len(dtypes)

        assert len(dtypes) == len(inner_fns)

        # Sort with a single element is just a copy
        if sizevars.statically_known_true(sympy.Le(sort_numel, 1)):
            return [
                Pointwise.create(
                    device=device,
                    dtype=dtypes[output_index],
                    inner_fn=inner_fns[output_index],
                    ranges=size,
                )
                for output_index in range(len(dtypes))
            ]

        def reindex(index: Sequence[Expr], sort_index: Sequence[Expr]) -> list[Expr]:
            assert len(sort_index) == len(sort_ranges)
            assert len(index) == len(pointwise_ranges)
            return [*index[:axis], *sort_index, *index[axis:]]

        results = [
            TensorBox.create(
                Sort(
                    device=device,
                    dtype=dtypes[output_index],
                    dtypes=dtypes,
                    inner_fn=inner_fns[output_index],
                    inner_fns=inner_fns,
                    size=size,
                    ranges=pointwise_ranges,
                    sort_ranges=sort_ranges,
                    reindex=reindex,
                    reduction_hint=reduction_hint,
                    output_index=output_index,
                    stable=stable,
                    descending=descending,
                    **kwargs,
                )
            )
            for output_index in range(len(dtypes))
        ]

        for result in results:
            result.realize()

        return results
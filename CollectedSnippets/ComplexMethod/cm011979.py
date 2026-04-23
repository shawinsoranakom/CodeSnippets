def create(  # type: ignore[override]
        cls,
        device: torch.device,
        dtypes: tuple[torch.dtype, ...],
        inner_fns: tuple[Callable[[Sequence[Expr]], Any], ...],
        size: list[Integer],
        axis: int,
        combine_fn: Callable[[tuple[Any, ...], tuple[Any, ...]], tuple[Any, ...]],
        reduction_hint: ReductionHint = ReductionHint.DEFAULT,
        *,
        # Whether we have the option to fallback to aten
        can_fallback_to_aten: bool = True,
        **kwargs: Any,
    ) -> Sequence[TensorBox | None]:
        pointwise_ranges = [*size[:axis], *size[axis + 1 :]]
        scan_ranges = [size[axis]]

        if not V.graph.has_feature(device, BackendFeature.SCAN):
            return [None] * len(dtypes)

        if len(dtypes) > 1 and not V.graph.has_feature(
            device, BackendFeature.TUPLE_REDUCTION
        ):
            return [None] * len(dtypes)

        sizevars = V.graph.sizevars
        scan_numel = sizevars.simplify(sympy_product(scan_ranges))

        assert len(dtypes) == len(inner_fns)

        # Scan with a single element is just a copy
        if sizevars.statically_known_true(sympy.Le(scan_numel, 1)):
            return [
                Pointwise.create(
                    device=device,
                    dtype=dtypes[output_index],
                    inner_fn=inner_fns[output_index],
                    ranges=size,
                )
                for output_index in range(len(dtypes))
            ]

        reduction_hint, num_splits = cls.num_splits(
            device=device,
            dtype=dtypes[0],
            inner_fn=inner_fns[0],
            axis=axis,
            pointwise_ranges=pointwise_ranges,
            scan_ranges=scan_ranges,
            combine_fn=combine_fn,
            scan_numel=scan_numel,
        )
        scan_type = Scan
        if num_splits > 1:
            supports_split = (
                # pyrefly: ignore [unsupported-operation]
                torch.version.hip is None or (has_triton and triton_version >= "3.3.0")
            ) and (len(dtypes) == 1)
            if not supports_split:
                if can_fallback_to_aten:
                    # Fallback to ATen
                    return [None] * len(dtypes)
                else:
                    num_splits = 1
            else:
                scan_type = SplitScan

        def reindex(index: Sequence[Expr], scan_index: Sequence[Expr]) -> list[Expr]:
            assert len(scan_index) == len(scan_ranges)
            assert len(index) == len(pointwise_ranges)
            return [*index[:axis], *scan_index, *index[axis:]]

        results = [
            TensorBox.create(
                scan_type(
                    device=device,
                    dtype=dtypes[output_index],
                    dtypes=dtypes,
                    inner_fn=inner_fns[output_index],
                    inner_fns=inner_fns,
                    size=size,
                    ranges=pointwise_ranges,
                    scan_ranges=scan_ranges,
                    combine_fn=combine_fn,
                    reindex=reindex,
                    reduction_hint=reduction_hint,
                    output_index=output_index,
                    **kwargs,
                )
            )
            for output_index in range(len(dtypes))
        ]

        for result in results:
            result.realize()

        return results
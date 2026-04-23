def create(
        cls,
        device: torch.device,
        dst_dtype: torch.dtype,
        src_dtype: torch.dtype,
        inner_fn: Callable[..., Any],
        ranges: Sequence[Expr],
        reduction_ranges: Sequence[Expr],
        reduction_type: ReductionType,
        reduction_hint: ReductionHint = ReductionHint.DEFAULT,
        input_node: IRNode | None = None,
    ) -> TensorBox:
        """
        Create a reduction node. May split the reduction to multiple layers to expose
        more parallelism.
        """
        reduction_numel = V.graph.sizevars.simplify(sympy_product(reduction_ranges))

        if reduction_numel == 0:
            # N.B. This is a hack to generate the literal of the given type
            # Ideally, we should be fixing `def constant` in triton.py
            # but it breaks due to hardcoded dtypes in other places
            def py_cnst(val: object) -> bool | float | int:
                if dst_dtype == torch.bool:
                    return bool(val)
                elif dst_dtype.is_floating_point:
                    assert isinstance(val, SupportsFloat), type(val)
                    return float(val)
                else:
                    assert isinstance(val, SupportsInt), type(val)
                    return int(val)

            rtypes_to_inits = {
                "sum": py_cnst(0),
                "xor_sum": py_cnst(0),
                "prod": py_cnst(1),
                "any": py_cnst(0),
                # "all" is desugared to `!any(!val)`
            }

            assert reduction_type in rtypes_to_inits, (
                f"{reduction_type} not supported for zero-dimension tensors!"
            )

            def const_fn(index: int) -> OpsValue:
                return ops.constant(rtypes_to_inits[reduction_type], dst_dtype)

            return Pointwise.create(
                device=device,
                dtype=src_dtype,
                inner_fn=const_fn,
                ranges=list(ranges),
            )

        if reduction_numel == 1:
            # this reduction is actually a pointwise op
            if reduction_type in ("argmin", "argmax"):

                def fn(index: int) -> OpsValue:
                    return ops.constant(0, dst_dtype)

            else:

                def fn(index: int) -> OpsValue:
                    reduction_index = [sympy.S.Zero for _ in reduction_ranges]
                    return inner_fn(index, reduction_index)

            return Pointwise.create(
                device=device, dtype=dst_dtype, inner_fn=fn, ranges=ranges
            )

        if (
            isinstance(reduction_numel, Integer)
            and int(reduction_numel) < config.unroll_reductions_threshold
            and (sympy_product(ranges) != 1 or is_gpu(device.type))
            and reduction_type != "dot"
        ):
            # When native matmul, don't unroll the dot reduction.

            # NB: This works around https://github.com/pytorch/pytorch/issues/140457
            # since turning reductions into pointwise ops can exacerbate this problem
            return Pointwise.create(
                device=device,
                dtype=dst_dtype,
                inner_fn=cls._unroll_reduction_fn(
                    inner_fn, reduction_ranges, reduction_type, src_dtype
                ),
                ranges=ranges,
            )

        # triton doesn't support reduce to single element well, so break it up
        hint, split = cls.num_splits(
            device,
            dst_dtype,
            src_dtype,
            inner_fn,
            ranges,
            reduction_ranges,
            reduction_type,
            reduction_numel,
            input_node,
        )

        def _maybe_increase_split(split: int) -> int:
            # don't apply min_num_split constraint for static shape case.
            if _is_static(reduction_numel):
                return split
            if split > 1:
                return max(split, config.min_num_split)
            else:
                return split

        split = _maybe_increase_split(split)

        # intermediate reduction in split can contain complex indexing,
        # and num_splits will fail to correctly set the hint
        # reuse the passed hint if available
        if reduction_hint == ReductionHint.DEFAULT:
            reduction_hint = hint
        if split == -1:
            assert input_node is not None
            with patch.object(FlexibleLayout, "allow_indexing", True):
                new_ranges, new_reduction_ranges = extract_input_node_reduction_ranges(
                    input_node
                )
            assert new_ranges is not None
            assert new_reduction_ranges is not None
            return cls.create_multilayer_existing_ranges(
                device,
                dst_dtype,
                src_dtype,
                inner_fn,
                ranges,
                reduction_ranges,
                new_ranges,
                new_reduction_ranges,
                reduction_type,
                reduction_hint,
            )
        elif split > 1:
            # triton doesn't support reduce to single element well, so break it up
            out = cls.create_multilayer(
                device,
                dst_dtype,
                src_dtype,
                inner_fn,
                ranges,
                reduction_ranges,
                reduction_type,
                split,
                reduction_hint,
                input_node,
            )

            # Find the reduction that get split
            split_reduction = None
            if config.triton.mix_order_reduction and isinstance(out, TensorBox):

                def _find_split_reduction(
                    cur_node: TensorBox,
                ) -> ComputedBuffer | None:
                    read_names = cur_node.get_read_names()
                    if len(read_names) != 1:
                        return None

                    bufname = next(iter(read_names))
                    if bufname not in V.graph.name_to_buffer:
                        return None
                    buf = V.graph.name_to_buffer[bufname]
                    if not isinstance(buf, ComputedBuffer):
                        return None

                    assert buf.data.get_reduction_type() is not None

                    return buf

                split_reduction = _find_split_reduction(out)

            if split_reduction:
                # If a reduction is split to more than 2 layers,
                # say there are 3 layers,
                # we always have the correct setting for layer1 (top layer).
                # The setting on layer2 may be incorrect but it's fine
                # since they are never get used.
                # TODO: should we skip setting these fields for layer2
                assert isinstance(split_reduction.data, Reduction), (
                    f"{type(split_reduction.data)}"
                )
                split_reduction._split_size = split_reduction.data.reduction_ranges[0]
                split_reduction._original_inner_fn = inner_fn
                split_reduction._original_ranges = ranges
                split_reduction._original_reduction_ranges = reduction_ranges
            return out

        out = TensorBox.create(
            Reduction(
                device=device,
                dtype=dst_dtype,
                inner_fn=inner_fn,
                ranges=ranges,
                reduction_ranges=reduction_ranges,
                reduction_type=reduction_type,
                src_dtype=src_dtype,
                reduction_hint=reduction_hint,
            )
        )
        return out
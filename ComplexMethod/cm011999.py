def require_strides(
        cls,
        x: IRNode,
        order: Sequence[int] | None = None,
        exact_strides: Sequence[_IntLike] | None = None,
        allow_padding: bool = False,
    ) -> IRNode:
        """Ensure x has the requested stride order or exact strides, inserting a copy if needed."""
        assert order is not None or exact_strides is not None
        # Layout generally doesn't matter, but some consuming external ops might have requirements
        if x.get_numel() in (0, 1) and not exact_strides:
            return x

        # require x to have the layout
        if is_storage_and_layout(x):
            if isinstance(x.get_layout(), FlexibleLayout):
                if order:
                    # If the FlexibleLayout already has the size and stride in the required order,
                    # freeze it to a FixedLayout by using its current size and stride.
                    # The behavior of using its current size and stride or the given order can be different
                    # if the size and stride has ambiguilty, for example for a 4D input where the iC = 1:
                    # size=[s0, 1, 28, 28], stride=[784, 784, 28, 1]. If the required order is [3, 0, 2, 1] (channels last),
                    # the current size and stride already satisfies this order.
                    # However by freezing it to the required order, the layout will be changed to:
                    # size=[s0, 1, 28, 28], stride=[784, 1, 28, 1]), which is not actually necessary.
                    use_current_stride_order = is_stride_order_storage_and_layout(
                        x, order
                    ) and not free_unbacked_symbols(x.get_layout().stride)
                    # fix flexiblelayout to be FixedLayout with stride_order
                    as_storage_and_layout(
                        x,
                        freeze=True,
                        want_contiguous=False,
                        stride_order=(
                            get_stride_order(
                                V.graph.sizevars.guarding_hints_or_throw(
                                    x.get_layout().stride
                                )
                            )
                            if use_current_stride_order
                            else order
                        ),
                        allow_padding=allow_padding,
                    )
                    return x
                else:
                    # If the exact_strides is given, freeze the FlexibleLayout to a FixedLayout with the exact_strides.
                    as_storage_and_layout(
                        x,
                        freeze=True,
                        want_contiguous=False,
                        stride_order=None,
                        allow_padding=allow_padding,
                        exact_strides=exact_strides,
                    )
                    return x

            # When padding is allowed, check if the buffer's existing strides
            # match padded versions of the requested strides (e.g. concat graph
            # outputs that were already padded by ConcatKernel).
            padded_exact_strides = None
            if allow_padding and exact_strides:
                padded_exact_strides = list(
                    Layout._pad_strides(exact_strides, x.get_size(), x.get_dtype())
                )

            if isinstance(x.get_layout(), (FixedLayout, NonOwningLayout)) and (
                (order and x.get_layout().is_stride_ordered(order))
                or (
                    exact_strides
                    and significant_strides_equal(
                        exact_strides, x.get_layout().stride, x.get_size()
                    )
                )
            ):
                return (
                    try_match_insignificant_strides(x, exact_strides)
                    if exact_strides is not None
                    else x
                )
            # Accept already-padded buffers when padding is allowed
            elif (
                padded_exact_strides is not None
                and isinstance(x.get_layout(), (FixedLayout, NonOwningLayout))
                and significant_strides_equal(
                    padded_exact_strides, x.get_layout().stride, x.get_size()
                )
            ):
                return try_match_insignificant_strides(x, padded_exact_strides)
            elif isinstance(
                (mutation_layout := x.get_layout()), MutationLayoutSHOULDREMOVE
            ):
                if isinstance(
                    (real_layout := mutation_layout.real_layout()), FlexibleLayout
                ):
                    raise AssertionError(
                        "the MutationLayoutSHOULDREMOVE's real layout shouldn't be FlexibleLayout"
                    )
                elif isinstance(real_layout, FixedLayout) and (
                    (order and real_layout.is_stride_ordered(order))
                    or (
                        exact_strides
                        and significant_strides_equal(
                            exact_strides, real_layout.stride, x.get_size()
                        )
                    )
                ):
                    return x

        # TODO - Storage to InputBuffer
        if isinstance(x, InputBuffer) and (
            (order and x.get_layout().is_stride_ordered(order))
            or (
                exact_strides
                and significant_strides_equal(
                    exact_strides, x.get_layout().stride, x.get_size()
                )
            )
        ):
            return x
        if (
            isinstance(x, TensorBox)
            and isinstance(x.data, BaseView)
            and not isinstance(x.data, ReinterpretView)
            and is_storage_and_layout(unwrap_view := x.unwrap_view())
            and hasattr(unwrap_view, "data")
            and not isinstance(unwrap_view.data, ExternKernelAlloc)
        ):
            try:
                x.data = cls.convert_to_reinterpret_view(x.data)
                if order:
                    return cls.require_stride_order(
                        x, order, allow_padding=allow_padding
                    )
                elif exact_strides:
                    return cls.require_exact_strides(
                        x, exact_strides, allow_padding=allow_padding
                    )
            except NotImplementedError:
                pass

        # Preserve ExpandView representation that would be lost during copy_input
        # Without representation of the expand in inductor IR, in codegen we end up
        # launching a grid for the full size tensor and doing redundant computation
        # across expanded dims.
        # TODO: could also be good to have a codegen fix to recognize overlapping elements

        expanded_dims: list[int] | None = None
        orig_size = x.get_size()
        if exact_strides is not None:
            sizevars = V.graph.sizevars
            expanded_dims = [
                i
                for i in range(len(x.get_size()))
                if sizevars.statically_known_equals(exact_strides[i], 0)
                and sizevars.statically_known_geq(x.get_size()[i], 2)
            ]

            for dim in expanded_dims:
                x = torch._inductor.lowering.slice_(x, dim, 0, 1)

        # Although this is a clone, inductor is good about fusing clones into previous
        # operations if they weren't realized and their layouts were flexible.
        x = cls.copy_input(x)

        as_storage_and_layout(
            x,
            freeze=True,
            want_contiguous=False,
            stride_order=order,
            allow_padding=allow_padding,
            exact_strides=exact_strides,
        )
        if order:
            assert is_stride_order_storage_and_layout(x, order)
        elif expanded_dims:
            assert orig_size is not None and exact_strides is not None
            x = torch._inductor.lowering.expand(x, orig_size)
            # the expand will sometimes may change insignificant strides, so match them back
            return try_match_insignificant_strides(x, exact_strides)

        return x
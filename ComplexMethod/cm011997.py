def convert_to_reinterpret_view(cls, x: IRNode) -> ReinterpretView:
        """
        In order to pass this to an extern kernel we need a
        ReinterpretView not a View.  This allows us to avoid some
        unneeded copies.
        """
        assert isinstance(x, BaseView), type(x)
        if isinstance(x, ReinterpretView):
            return x

        # NOTE: Don't use extract_read_writes here as it fails when
        # make_loader() inlines the computation
        x_unwrap_view = x.unwrap_view()
        buf = V.graph.get_buffer(x_unwrap_view.get_name())
        assert buf is not None
        x_unwrap_view_fx_node = buf.get_origin_node()
        # Prefer channels last format according to how the format is set from eager.
        if (
            x_unwrap_view_fx_node is not None
            and "val" in x_unwrap_view_fx_node.meta
            and isinstance(x_unwrap_view, (ReinterpretView, Buffer, MutableBox))
            and isinstance(x_unwrap_view.layout, FlexibleLayout)
            and (
                is_contiguous_for_memory_format_or_false(
                    x_unwrap_view_fx_node.meta["val"],
                    memory_format=torch.channels_last,
                )
                or is_contiguous_for_memory_format_or_false(
                    x_unwrap_view_fx_node.meta["val"],
                    memory_format=torch.channels_last_3d,
                )
            )
        ):
            x_unwrap_view.freeze_layout_with_same_order(
                make_channels_last_strides_for(x_unwrap_view.get_size())
            )
        else:
            x_unwrap_view.freeze_layout()

        index_args, var_ranges = dependencies.index_vars_squeeze(
            x.get_size(), prefix="r"
        )
        range_vars = index_args[0]
        index = x.make_indexer()(range_vars)

        index = V.graph.sizevars.simplify_with_ranges(index, var_ranges)
        strides = V.graph.sizevars.stride_vars(index, range_vars)
        offset = V.graph.sizevars.offset_var(index, range_vars)
        expected = sympy_dot(range_vars, strides) + offset

        if index != expected:
            log.debug(
                "convert_to_reinterpret_view failed: stride=%s offset=%s index=%s",
                strides,
                offset,
                index,
            )
            raise NotImplementedError

        return ReinterpretView(
            data=x.data,
            layout=FixedLayout(
                device=x.get_device_or_error(),
                dtype=x.get_dtype(),
                size=x.get_size(),
                stride=strides,
                offset=offset,
                is_pinned=False,
            ),
        )
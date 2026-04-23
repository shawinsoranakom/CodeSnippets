def make_key(
        self,
        input_nodes: tuple[ir.IRNode, ...],
        num_stages: int,
        num_warps: int,
        call_sizes: Sequence[sympy.core.symbol.Symbol],
        prefix_args: int,
        suffix_args: int,
        epilogue_fn: Callable[..., Any] | None,
        epilogue_fn_hash: str | None,
        tma_store: bool,
        transpose_discontiguous_tensor_descriptors_override: bool | None,
        subgraphs: list[ir.Buffer] | None,  # has to be none to cache
        workspace_arg: WorkspaceArg | None,  # has to be none to cache
        layout: ir.Layout,
        num_consumer_groups: int,
        num_buffers_warp_spec: int,
        kwargs: dict[str, Any],
        hint_override: int | None = None,
        triton_meta: dict[str, Any] | None = None,
    ) -> str | None:
        def layout_key(layout: ir.Layout) -> str:
            assert not isinstance(layout, ir.FlexibleLayout)
            return repr(
                [
                    layout.size,
                    layout.stride,
                    layout.dtype,
                    layout.device,
                    layout.offset,
                ]
            )

        def has_flexible_layout() -> bool:
            if isinstance(layout, ir.FlexibleLayout):
                return True

            for input in input_nodes:
                if isinstance(input.get_layout(), ir.FlexibleLayout):
                    return True
            return False

        if epilogue_fn is identity:
            assert epilogue_fn_hash is None
            epilogue_fn_hash = "identity"

        # we do not cache under those conditions right now.
        if (
            has_flexible_layout()
            or subgraphs is not None
            or workspace_arg is not None
            or epilogue_fn_hash is None
        ):
            return None

        return repr(
            {
                "input_nodes": [
                    layout_key(input.get_layout()) for input in input_nodes
                ],
                "num_stages": num_stages,
                "num_warps": num_warps,
                "prefix_args": prefix_args,
                "suffix_args": suffix_args,
                "call_sizes": call_sizes,
                "layout": layout_key(layout),
                "num_consumer_groups": num_consumer_groups,
                "num_buffers_warp_spec": num_buffers_warp_spec,
                "epilogue_fn_hash": epilogue_fn_hash,
                "tma_store": tma_store,
                "transpose_discontiguous_tensor_descriptors_override": transpose_discontiguous_tensor_descriptors_override,
                "kwargs": kwargs,
                "hint_override": hint_override,
                "triton_meta": triton_meta,
            }
        )
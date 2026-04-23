def mark_nodes_dislike_padding(
    g: Graph, user_visible_output_strides: dict[Node, tuple[int, ...]]
) -> None:
    """
    Nodes like convolution/convolution_backward want its input to be dense.
    If we pad their inputs, we result in extra calls to copy kernels!  On the other hand, padding usually helps reduction.

    The pass finds nodes that dislike padding. These are nodes that can be reached
    from a convolution/convolution_backward in the backward direction without
    going thru a reduction.
    """
    if not config.comprehensive_padding:
        return

    extended_user_visible_nodes = extend_user_visible_output_strides(
        user_visible_output_strides
    )
    ops_dislike_padding = OrderedSet(
        [
            aten.convolution,
            aten.convolution_backward,
            aten._scaled_mm,
        ]
    )
    # what's a better way to collect the reduction ops?
    ops_like_padding = OrderedSet(
        [
            aten.var_mean,
            aten.sum,
            aten.mean,
            aten.prod,
            aten.any,
            aten.amin,
            aten.amax,
            aten.min,
            aten.max,
            aten.argmin,
            aten.argmax,
            aten.scatter_reduce,
        ]
    )

    def _get_overload_packet(
        node: torch.fx.Node,
    ) -> torch._ops.OpOverloadPacket | None:
        return (
            node.target._overloadpacket
            if node.op == "call_function"
            # hasattr on OpOverloadPacket is slow, do isinstance first
            and isinstance(node.target, torch._ops.OpOverload)
            and hasattr(node.target, "_overloadpacket")
            else None
        )

    for cur in reversed(g.nodes):
        if isinstance(
            cur.target,
            torch._higher_order_ops.triton_kernel_wrap.TritonKernelWrapperMutation,
        ):
            cur.meta["dislike_padding"] = True
            continue

        if (
            isinstance(cur.target, torch._ops.OpOverload)
            and get_layout_constraint_tag(cur.target)
            == torch._C.Tag.needs_exact_strides
        ):
            cur.meta["dislike_padding"] = True
            continue

        op = _get_overload_packet(cur)
        if not op:
            continue
        if op in ops_dislike_padding:
            cur.meta["dislike_padding"] = True

        if cur.meta.get("dislike_padding", False):
            # propagate
            for prior in cur.all_input_nodes:
                prior_op = _get_overload_packet(prior)
                if not prior_op:
                    continue
                if prior_op not in ops_like_padding:
                    prior.meta["dislike_padding"] = True
        # We only want to mark output nodes. So, move it after the above prior nodes process.
        if not config.pad_outputs and cur in extended_user_visible_nodes:
            # Reductions (ops_like_padding) produce new output buffers with
            # fresh strides, so their output stride constraint is already
            # enforced by allow_padding=False in as_exact_strides. Setting
            # dislike_padding here would suppress input padding during
            # freeze, causing a stride mismatch when an earlier lowering
            # step (e.g. is_contiguous_storage_and_layout) already mutated
            # the input layout to padded strides.
            if op not in ops_like_padding:
                cur.meta["dislike_padding"] = True
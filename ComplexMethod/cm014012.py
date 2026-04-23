def check_pt2_compliant_op(
    output_graph: OutputGraph, kind: str, target: Any, args: Any, kwargs: Any
) -> None:
    if kind != "call_function":
        return

    def encountered_compliant_op(target: torch._ops.OpOverload) -> None:
        if target.namespace in {"prim", "prims", "aten"}:
            return
        output_graph.compliant_custom_ops.add(target)

    def encountered_non_compliant_op(target: torch._ops.OpOverload, msg: str) -> None:
        output_graph.non_compliant_ops.add(target)
        if config.only_allow_pt2_compliant_ops:
            unimplemented(
                gb_type="Encountered non-PT2-compliant op",
                context="",
                explanation=msg + " " + err_epilogue,
                hints=[],
            )

    if isinstance(target, torch._ops.OpOverload):
        if torch.Tag.pt2_compliant_tag in target.tags:
            encountered_compliant_op(target)
            return
        encountered_non_compliant_op(
            target,
            f"Encountered the torch.ops.OpOverload {target} that is not PT2 compliant.",
        )
        return

    if isinstance(target, torch._ops.OpOverloadPacket):
        overloads = tuple(target.overloads())
        # Optimization: Overload resolution is expensive.
        # If there's only one overload, we know what it will resolve to.
        if len(overloads) == 1:
            op = getattr(target, overloads[0])
            if torch.Tag.pt2_compliant_tag in op.tags:
                encountered_compliant_op(op)
                return
            encountered_non_compliant_op(
                op,
                f"Encountered the non-overloaded "
                f"torch.ops.OpOverloadPacket {target} "
                f"that is not PT2 compliant. ",
            )
            return

        args, kwargs = torch._dynamo.utils.get_fake_values_from_nodes(
            output_graph.current_tx, (args, kwargs), False
        )
        try:
            overload = torch._C._jit_resolve_packet(
                target._qualified_op_name, *args, **kwargs
            )
        except RuntimeError as e:
            unimplemented(
                gb_type="Error when attempting to resolve op packet",
                context="",
                explanation=str(e),
                hints=[],
            )

        op = getattr(target, overload)
        if torch.Tag.pt2_compliant_tag in op.tags:
            encountered_compliant_op(op)
        else:
            encountered_non_compliant_op(
                op,
                f"Encountered the torch.ops.OpOverloadPacket {target} "
                f"which resolves to the overload ({overload}) that is "
                f"not PT2 compliant.",
            )
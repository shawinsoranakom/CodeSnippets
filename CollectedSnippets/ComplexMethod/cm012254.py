def remove_no_ops(
    gm: torch.fx.GraphModule,
    zeros: OrderedSet[torch.fx.Node],
    ones: OrderedSet[torch.fx.Node],
):
    """Remove identity arithmetic operations: (+ 0, - 0, * 1, / 1)."""
    with torch.utils._python_dispatch._disable_current_modes():
        graph = gm.graph

        def fake_tensors_eq(t1, t2, fields=("shape", "dtype", "device")):
            if any(not isinstance(t, torch.Tensor) for t in (t1, t2)):
                return False
            for field in fields:
                if getattr(t1, field) != getattr(t2, field):
                    return False
            return True

        def is_mutated(n):
            """Check if a node is mutated by any in-place operation."""
            for user in n.users:
                if user.op != "call_function" or not hasattr(user.target, "_schema"):
                    continue
                for i, arg in enumerate(user.args):
                    if arg is n:
                        schema_arg = user.target._schema.arguments[i]
                        if schema_arg.alias_info and schema_arg.alias_info.is_write:
                            return True
            return False

        def replace_no_op(node, replace_input_index):
            replacement = node.args[replace_input_index]

            # https://github.com/pytorch/pytorch/issues/86128 causes
            # non-Tensor inputs even for ops with only Tensor inputs.
            # TODO - decompose/type promote to avoid this
            if not all(isinstance(arg, torch.fx.Node) for arg in node.args):
                return

            # https://github.com/pytorch/pytorch/issues/174187
            # Don't replace if the replacement value is mutated in-place.
            # The original node acts as an implicit copy; removing it would
            # cause users to observe the post-mutation value instead.
            if is_mutated(replacement):
                return

            if not fake_tensors_eq(node.meta["val"], replacement.meta["val"]):
                if fake_tensors_eq(
                    node.meta["val"],
                    replacement.meta["val"],
                    ("shape", "device"),
                ):
                    with graph.inserting_after(node):
                        replacement = graph.call_function(
                            torch.ops.prims.convert_element_type.default,
                            args=(replacement, node.meta["val"].dtype),
                        )
                else:
                    return

            node.replace_all_uses_with(replacement)
            replacement.meta.update(node.meta)
            graph.erase_node(node)

        for node in graph.find_nodes(op="call_function", target=aten.add.Tensor):
            # TODO handle Tensor-Scalar adds, it's a different schema
            if len(node.args) == 2:
                if (
                    not any(e in zeros for e in node.args)
                    or node.kwargs.get("alpha", 1) != 1
                ):
                    continue

                replace_index = 1 if node.args[0] in zeros else 0
                replace_no_op(node, replace_index)

        for node in graph.find_nodes(op="call_function", target=aten.sub.Tensor):
            if len(node.args) == 2:
                if node.args[1] not in zeros or node.kwargs.get("alpha", 1) != 1:
                    continue

                replace_no_op(node, 0)

        for node in graph.find_nodes(op="call_function", target=aten.mul.Tensor):
            if len(node.args) == 2:
                if not any(e in ones for e in node.args):
                    continue

                replace_input_index = 1 if node.args[0] in ones else 0
                replace_no_op(node, replace_input_index)

        for node in graph.find_nodes(op="call_function", target=aten.div.Tensor):
            if len(node.args) == 2 and node.args[1] in ones:
                replace_no_op(node, 0)

        # meta tensors returned from the graph have no data and can be replaced with empty_strided
        for output_node in graph.find_nodes(op="output"):
            had_meta_return = False

            def visit(n):
                nonlocal had_meta_return
                val = n.meta.get("val")
                if isinstance(val, torch.Tensor) and val.device.type == "meta":
                    with graph.inserting_before(output_node):
                        n.replace_all_uses_with(
                            graph.call_function(
                                torch.ops.aten.empty_strided.default,
                                args=(val.size(), val.stride()),
                                kwargs={"dtype": val.dtype, "device": val.device},
                            )
                        )
                    had_meta_return = True

            torch.fx.map_arg(output_node.args, visit)
            if had_meta_return:
                graph.eliminate_dead_code()
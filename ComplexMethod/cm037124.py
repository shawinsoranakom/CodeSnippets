def _decompose_size_nodes(graph: fx.GraphModule) -> None:
    """Decompose x.size() into per-dim sym_size.int calls.

    torch.Size objects cannot cross split boundaries because aot_autograd
    cannot handle them as submodule outputs. This replaces each size() call
    with individual sym_size.int(x, dim) nodes:
      - Dynamic dims (SymInt) → new sym_size.int node
      - Static dims (plain int) → inlined as literal constant
    """
    # Dynamo captures x.size()/x.shape as call_method target="size".
    size_nodes = list(graph.graph.find_nodes(op="call_method", target="size"))

    for node in size_nodes:
        tensor_node = node.args[0]
        ev = tensor_node.meta.get("example_value")
        assert ev is not None, (
            f"Tensor node '{tensor_node.name}' has no example_value metadata. "
            f"Cannot decompose size node '{node.name}'."
        )

        # Build per-dim replacements: sym_size.int node or literal int.
        dims: list[fx.Node | int] = []
        with graph.graph.inserting_after(tensor_node):
            for i in range(ev.dim()):
                dim_val = ev.shape[i]
                if isinstance(dim_val, torch.SymInt):
                    dn = graph.graph.call_function(
                        torch.ops.aten.sym_size.int, args=(tensor_node, i)
                    )
                    dn.meta["example_value"] = dim_val
                    dims.append(dn)
                elif isinstance(dim_val, int):
                    dims.append(dim_val)
                else:
                    raise AssertionError(
                        f"dim_val is either torch.SymInt or int, "
                        f"got {type(dim_val)} for dim {i} of "
                        f"'{node.name}'"
                    )

        # Replace size node in each user's args.
        for user in list(node.users):
            if (
                user.op == "call_function"
                and user.target is operator.getitem
                and len(user.args) == 2
                and user.args[0] is node
            ):
                # getitem(size, idx) → replace with dims[idx] directly.
                idx = user.args[1]
                assert isinstance(idx, int), (
                    f"Expected literal int index for getitem on size(), "
                    f"got {type(idx).__name__}: {idx}"
                )
                user.replace_all_uses_with(dims[idx])
                graph.graph.erase_node(user)
            else:
                # User consumes the full size tuple (e.g. view(clone, size))
                # → view(clone, d0, d1, ...)
                new_args = []
                for arg in user.args:
                    if arg is node:
                        new_args.extend(dims)
                    else:
                        new_args.append(arg)
                user.args = tuple(new_args)
        graph.graph.erase_node(node)
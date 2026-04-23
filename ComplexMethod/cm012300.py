def decompose_auto_functionalized(graph):
    """Decomposes auto_functionalized nodes into clones and the underlying
    mutation node.

    We assume that the reinplacing pass runs before this; the reinplacing pass
    tells us (via rewriting the arguments or .meta to those nodes) which
    Tensors we should clone and which Tensors are safe to reinplace.
    """
    graph_pass = PatternMatcherPass()

    @register_graph_pattern(
        CallFunctionVarArgs(torch.ops.higher_order.auto_functionalized),
        # pyrefly: ignore [bad-argument-type]
        pass_dict=graph_pass,
    )
    def _(match: Match, *args, **kwargs):
        from torch._higher_order_ops.auto_functionalize import auto_functionalized_dense

        only_clone_these_tensors = tuple(
            match.nodes[0].meta.get("only_clone_these_tensors", [])
        )

        flat_args, spec = pytree.tree_flatten((args, kwargs))

        # NB: we combine (args, kwargs) into flat args for replacing.
        # This is replace_by_example uses make_fx which does not support
        # tracing a function with kwargs.
        def decomp(*flat_args):
            args, kwargs = pytree.tree_unflatten(flat_args, spec)
            assert len(args) == 1
            mode = args[0]
            return auto_functionalized_dense(mode, only_clone_these_tensors, **kwargs)

        # pyrefly: ignore [bad-argument-type]
        match.replace_by_example(decomp, flat_args, run_functional_passes=False)

    @register_graph_pattern(
        CallFunctionVarArgs(torch.ops.higher_order.auto_functionalized_v2),
        # pyrefly: ignore [bad-argument-type]
        pass_dict=graph_pass,
    )
    def _(match: Match, *args, **kwargs):
        from torch._higher_order_ops.auto_functionalize import (
            auto_functionalized_v2_dense,
        )

        only_clone_these_bases = tuple(
            match.nodes[0].meta.get("only_clone_these_tensors", [])
        )

        flat_args, spec = pytree.tree_flatten((args, kwargs))

        def _maybe_resolve_constant_get_attr(node):
            # Resolve getattr node to its value because they don't always have meta["val"]
            if (
                isinstance(node, torch.fx.Node)
                and node.op == "get_attr"
                and "val" not in node.meta
            ):
                const_attr = getattr(graph.owning_module, node.target)  # type: ignore[arg-type]
                assert isinstance(
                    const_attr, (torch.fx.GraphModule, pytree.TreeSpec)
                ), (type(const_attr), const_attr)
                return const_attr
            return node

        flat_args = [_maybe_resolve_constant_get_attr(arg) for arg in flat_args]

        # NB: we combine (args, kwargs) into flat args for replacing.
        # This is replace_by_example uses make_fx which does not support
        # tracing a function with kwargs.
        def decomp(*flat_args):
            args, kwargs = pytree.tree_unflatten(flat_args, spec)
            assert len(args) == 1
            mutable_op = args[0]
            return auto_functionalized_v2_dense(
                mutable_op, only_clone_these_bases, **kwargs
            )

        # pyrefly: ignore [bad-argument-type]
        match.replace_by_example(decomp, flat_args, run_functional_passes=False)

    graph_pass.apply(graph)

    # Remove unused get_attr nodes and their corresponding attributes from the graph module.
    # When auto_functionalizing a hop, we need to clean up get_attr nodes for _constant_schema
    # and the auto_functionalized graph module that are no longer referenced.
    unused_get_attr_nodes = []
    removable_attrs: OrderedSet[torch.fx.node.Target] = OrderedSet()
    protected_attrs: OrderedSet[torch.fx.node.Target] = OrderedSet()

    # First pass: identify unused get_attr nodes and track attribute usage
    for node in graph.nodes:
        if node.op != "get_attr":
            continue

        if len(node.users) == 0:
            # Node is unused, mark for removal
            unused_get_attr_nodes.append(node)

            # Check if the attribute can be removed from the module
            if (
                hasattr(graph.owning_module, node.target)
                and isinstance(
                    getattr(graph.owning_module, node.target), torch.fx.GraphModule
                )
                and node.target not in protected_attrs
            ):
                removable_attrs.add(node.target)
        else:
            # Node is used, protect its attribute from removal
            if node.target in removable_attrs:
                removable_attrs.remove(node.target)
            protected_attrs.add(node.target)

    # Second pass: clean up unused nodes and attributes
    for node in unused_get_attr_nodes:
        graph.erase_node(node)

    for attr_name in removable_attrs:
        assert isinstance(attr_name, str)
        delattr(graph.owning_module, attr_name)

    graph.lint()

    for _ in graph.find_nodes(
        op="call_function", target=torch.ops.higher_order.auto_functionalized
    ):
        raise AssertionError("auto_functionalized was not removed")

    for _ in graph.find_nodes(
        op="call_function", target=torch.ops.higher_order.auto_functionalized_v2
    ):
        raise AssertionError("auto_functionalized_v2 was not removed")
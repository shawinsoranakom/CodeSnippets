def constant_fold(
    gm: torch.fx.GraphModule,
    constraint_fn: Callable[[torch.fx.Node], bool] | None = None,
) -> None:
    with torch.utils._python_dispatch._disable_current_modes():
        cf = ConstantFolder(gm, skip_constructors=True)
        cf.run()

        for node, constant in cf.node_replacements.items():
            if constraint_fn is not None and not constraint_fn(node):
                continue
            replace_node_with_constant(gm, node, constant)

        erased_params = []
        for node in gm.graph.find_nodes(op="get_attr"):
            if len(node.users) == 0:
                if hasattr(gm, node.target):
                    delattr(gm, node.target)
                erased_params.append(node)

        for node in erased_params:
            gm.graph.erase_node(node)

        gm.graph.eliminate_dead_code()
        gm.graph.lint()
        gm.recompile()
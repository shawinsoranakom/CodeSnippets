def constant_fold(
    gm: torch.fx.GraphModule,
    constraint_fn: Callable[[torch.fx.Node], bool] | None = None,
):
    with torch.utils._python_dispatch._disable_current_modes():
        cf = ConstantFolder(gm, skip_constructors=True)
        cf.run()

        for node, constant in cf.node_replacements.items():
            if constraint_fn is not None and not constraint_fn(node):
                continue
            replace_node_with_constant(gm, node, constant)

        erased_params = []
        # Get all attr users by looking up the graph instead from node.users, because in this case
        # _tensor_constant0 and _tensor_constant0_1 are actually refereing to the same tensor.

        #     opcode         name                 target            args                         kwargs
        # -------------  -------------------  ----------------  ---------------------------  --------
        # placeholder    arg0_1               arg0              ()                           {}
        # get_attr       _tensor_constant0    state             ()                           {}
        # call_function  add                  aten.add.Tensor   (arg0_1, _tensor_constant0)  {}
        # get_attr       _tensor_constant0_1  state             ()                           {}
        # call_function  add_                 aten.add_.Tensor  (_tensor_constant0_1, 1)     {}
        # output         output               output            ([add],)                     {}

        get_attr_node_users = defaultdict(list)
        for node in gm.graph.nodes:
            if node.op == "get_attr":
                get_attr_node_users[node.target].extend(node.users.keys())
        for node in gm.graph.find_nodes(op="get_attr"):
            if node.op == "get_attr" and len(get_attr_node_users[node.target]) == 0:
                if hasattr(gm, node.target):
                    delattr(gm, node.target)
                erased_params.append(node)
        for node in erased_params:
            gm.graph.erase_node(node)

        gm.graph.eliminate_dead_code()
        gm.graph.lint()
        gm.recompile()
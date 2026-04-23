def b2b_gemm_handler(match: Match, mat1: torch.fx.Node, mat2: torch.fx.Node) -> None:
    # match.args: list[torch.fx.Node]

    def is_pointwise_node(node: torch.fx.Node) -> bool:
        return (
            node.op == "call_function"
            and isinstance(node.target, torch._ops.OpOverload)
            and (torch.Tag.pointwise in node.target.tags)
        )

    def is_mm(node: torch.fx.Node) -> bool:
        return node.target is torch.ops.aten.mm.default

    # the inner MM
    inner_mm = match.nodes[-1]

    # find the (candidate) outer MM, which will be re-checked below to ensure every path reaches it
    # In a real (A @ f(B @ C)), every path starting from (B @ C) must reach (A @ _).
    outer_mm = None
    node = inner_mm
    while len(node.users) > 0:
        node = next(iter(node.users))
        if is_mm(node):
            outer_mm = node
            break
        elif is_pointwise_node(node):
            continue
        else:
            break
    if not outer_mm:
        return

    # find the unique input node for outer_mm representing f(B @ C) in (A @ f(B @ C))
    # we call it the "f_node"
    # when the pattern is simply (A @ (B @ C)), f_node is just inner_mm
    f_node = inner_mm
    while next(iter(f_node.users)) is not outer_mm:
        f_node = next(iter(f_node.users))

    def all_reach_via_pointwise_with_no_other_inputs(
        src: torch.fx.Node,
        dst: torch.fx.Node,
    ) -> tuple[bool, OrderedSet[torch.fx.Node]]:
        """
        check whether every user path from src reaches dst via pointwise nodes,
        with no other input nodes for the intermediates and dst;
        return
        (1) the Boolean value
        (2) the subgraph node set including src and dst (which only makes sense when the Boolean value is True)
        """
        visited = OrderedSet[torch.fx.Node]()
        input_counter: dict[torch.fx.Node, int] = {}

        all_reachable = True
        queue = deque([src])
        while queue:
            node = queue.popleft()
            if node not in visited:
                if node is dst:
                    visited.add(node)
                elif (node is src) or is_pointwise_node(node):
                    for user in node.users:
                        # for nodes other than dst, bookkeep their users' input counts
                        if user not in input_counter:
                            input_counter[user] = len(user.all_input_nodes)
                        input_counter[user] -= 1
                        # continue BFS
                        queue.append(user)
                    visited.add(node)
                else:
                    all_reachable = False
                    break

        return (
            all_reachable and all(count == 0 for count in input_counter.values()),
            visited,
        )

    # check inner_mm reaches f_node on every user path via pointwise nodes with no outside input_nodes
    ok, subgraph_node_set = all_reach_via_pointwise_with_no_other_inputs(
        inner_mm, f_node
    )
    if not ok:
        return

    # check inner_mm's inputs and f_node's outputs
    if not (len(inner_mm.all_input_nodes) == 2 and len(f_node.users) == 1):
        return

    # at this point, the nodes between inner_mm and f_node (both included)
    # are all used internally inside (A @ subgraph(B @ C))
    # i.e. they neither have other users nor have other inputs

    # original graph and module
    graph, module = inner_mm.graph, inner_mm.graph.owning_module

    # construct the new (sub)graph
    subgraph_node_list: list[
        torch.fx.Node
    ] = []  # ordered list of nodes used for node removal later
    new_graph: torch.fx.Graph = torch.fx.Graph()
    node_remapping: dict[torch.fx.Node, torch.fx.Node] = {}
    new_input_anchor: torch.fx.Node  # inner_mm, to be changed to an input node
    new_output_anchor: torch.fx.Node  # f_node, to be used to construct an output node
    new_input_node: torch.fx.Node
    new_output_node: torch.fx.Node
    for node in graph.nodes:  # preserve the order of nodes
        if node in subgraph_node_set:
            subgraph_node_list.append(node)
            new_node = new_graph.node_copy(node, lambda x: node_remapping.get(x, x))
            node_remapping[node] = new_node
            if node is inner_mm:
                new_input_anchor = new_node
            if node is f_node:
                new_output_anchor = new_node
    # pyrefly: ignore [unbound-name]
    if new_input_anchor is not new_output_anchor:  # subgraph is non-trivial
        # update the input node
        # pyrefly: ignore [unbound-name]
        with new_graph.inserting_before(new_input_anchor):
            new_input_node = new_graph.placeholder(name="subgraph_input")
            # pyrefly: ignore [unbound-name]
            new_input_node.meta.update(new_input_anchor.meta)
            # pyrefly: ignore [unbound-name]
            new_input_anchor.replace_all_uses_with(new_input_node)
        # pyrefly: ignore [unbound-name]
        new_graph.erase_node(new_input_anchor)
        # add the output node
        # pyrefly: ignore [unbound-name]
        new_output_node = new_graph.output(new_output_anchor)
        # pyrefly: ignore [unbound-name]
        new_output_node.meta.update(new_output_anchor.meta)
    else:  # subgraph is trivial, e.g. (A @ (B @ C))
        # update the input node
        # pyrefly: ignore [unbound-name]
        with new_graph.inserting_before(new_input_anchor):
            new_input_node = new_graph.placeholder(name="subgraph_input")
            # pyrefly: ignore [unbound-name]
            new_input_node.meta.update(new_input_anchor.meta)
            # pyrefly: ignore [unbound-name]
            new_input_anchor.replace_all_uses_with(new_input_node)
        # pyrefly: ignore [unbound-name]
        new_graph.erase_node(new_input_anchor)
        # update the output node (don't use new_output_anchor since it has been erased)
        new_output_node = new_graph.output(new_input_node)
        new_output_node.meta.update(new_input_node.meta)
    new_graph.lint()

    # construct the subgraph
    subgraph = Subgraph(
        name="subgraph", graph_module=torch.fx.GraphModule(module, new_graph)
    )

    # two cases
    # (1) (subgraph(A @ B) @ C), called "left_assoc"
    # (2) (A @ subgraph(B @ C)), called "right_assoc"
    is_left_assoc = outer_mm.args[0] is f_node

    # find the nodes A, B, C and check the sizes
    A: torch.fx.Node
    B: torch.fx.Node
    C: torch.fx.Node
    if is_left_assoc:
        A = inner_mm.args[0]  # type: ignore[assignment]
        B = inner_mm.args[1]  # type: ignore[assignment]
        C = outer_mm.args[1]  # type: ignore[assignment]
    else:
        A = outer_mm.args[0]  # type: ignore[assignment]
        B = inner_mm.args[0]  # type: ignore[assignment]
        C = inner_mm.args[1]  # type: ignore[assignment]
    if not is_b2b_gemm_good_on(is_left_assoc, A, B, C):
        return

    # finally update the original graph
    counters["inductor"]["b2b_gemm"] += 1
    graph = match.graph
    with graph.inserting_before(outer_mm):
        function = functools.partial(tuned_b2b_gemm, is_left_assoc, subgraph)
        function.__name__ = tuned_b2b_gemm.__name__  # type: ignore[attr-defined]
        function._inductor_lowering_function = True  # type: ignore[attr-defined]
        replacement: torch.fx.Node = graph.call_function(
            function,
            (A, B, C),
            match.kwargs,
        )
        replacement.meta.update(outer_mm.meta)
        outer_mm.replace_all_uses_with(replacement)
    # erase unnecessary nodes
    graph.erase_node(outer_mm)
    for node in reversed(subgraph_node_list):
        graph.erase_node(node)
    graph.lint()
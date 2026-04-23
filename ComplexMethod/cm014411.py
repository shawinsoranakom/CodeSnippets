def parse(graph, trace, args=None, omit_useless_nodes=True):
    """Parse an optimized PyTorch model graph and produces a list of nodes and node stats.

    Useful for eventual conversion to TensorBoard protobuf format.

    Args:
      graph (PyTorch module): The model graph to be parsed.
      trace (PyTorch JIT TracedModule): The model trace to be parsed.
      args (tuple): input tensor[s] for the model.
      omit_useless_nodes (boolean): Whether to remove nodes from the graph.
    """
    nodes_py = GraphPy()
    for node in graph.inputs():
        if omit_useless_nodes:
            if (
                len(node.uses()) == 0
            ):  # number of user of the node (= number of outputs/ fanout)
                continue

        if node.type().kind() != CLASSTYPE_KIND:
            nodes_py.append(NodePyIO(node, "input"))

    attr_to_scope: dict[Any, str] = {}
    for node in graph.nodes():
        if node.kind() == GETATTR_KIND:
            attr_name = node.s("name")
            attr_key = node.output().debugName()
            parent = node.input().node()
            if (
                parent.kind() == GETATTR_KIND
            ):  # If the parent node is not the top-level "self" node
                parent_attr_key = parent.output().debugName()
                parent_scope = attr_to_scope[parent_attr_key]
                attr_scope = parent_scope.split("/")[-1]
                attr_to_scope[attr_key] = f"{parent_scope}/{attr_scope}.{attr_name}"
            else:
                attr_to_scope[attr_key] = f"__module.{attr_name}"
            # We don't need classtype nodes; scope will provide this information
            if node.output().type().kind() != CLASSTYPE_KIND:
                node_py = NodePyOP(node)
                node_py.scopeName = attr_to_scope[attr_key]  # type: ignore[attr-defined]
                nodes_py.append(node_py)
        else:
            nodes_py.append(NodePyOP(node))

    for i, node in enumerate(graph.outputs()):  # Create sink nodes for output ops
        node_pyio = NodePyIO(node, "output")
        node_pyio.debugName = f"output.{i + 1}"
        node_pyio.inputs = [node.debugName()]
        nodes_py.append(node_pyio)

    def parse_traced_name(module):
        if isinstance(module, torch.jit.TracedModule):
            module_name = module._name
        else:
            module_name = getattr(module, "original_name", "Module")
        return module_name

    alias_to_name = {}
    base_name = parse_traced_name(trace)
    for name, module in trace.named_modules(prefix="__module"):
        mod_name = parse_traced_name(module)
        attr_name = name.split(".")[-1]
        alias_to_name[name] = f"{mod_name}[{attr_name}]"

    for node in nodes_py.nodes_op:
        module_aliases = node.scopeName.split("/")
        replacements = [
            alias_to_name[alias] if alias in alias_to_name else alias.split(".")[-1]
            for alias in module_aliases
        ]
        node.scopeName = base_name
        if any(replacements):
            node.scopeName += "/" + "/".join(replacements)

    nodes_py.populate_namespace_from_OP_to_IO()
    return nodes_py.to_proto()
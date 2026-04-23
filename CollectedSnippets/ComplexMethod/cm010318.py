def _sink_params(
    module: torch.nn.Module,
    inputs_to_state: dict[str, list[str]],
    scope: list[str],
    module_id_to_inputs_removed: dict[int, set[str]] | None = None,
):
    """Sink params, buffers, and constants from graph inputs into get_attr nodes.

    Exported modules are purely functional, so they pass their parameters and
    buffers in as inputs to the graph.

    To replicate eager's semantics, we need to get them from the module state
    via get_attr instead.

    module: GraphModule, potentially containing nested submodules.
    inputs_to_state: mapping graph input names to the corresponding key in the state_dict.
    scope: tracks where we are in the module hierarchy, so that we can emit the
        right `getattr(self, "foo.bar")` calls, etc.
    module_id_to_inputs_removed: records inputs removed by child modules, mapping
        the module object id to the list of placeholder node names in the child module
        that were removed.
    """
    if module_id_to_inputs_removed is None:
        module_id_to_inputs_removed = defaultdict(set)

    if id(module) in module_id_to_inputs_removed:
        return {id(module): module_id_to_inputs_removed[id(module)]}

    # We need to use _modules here instead of named_children(), because we
    # explicitly want duplicate modules to show up in the traversal.
    for name, submodule in module._modules.items():
        submod_id_to_inputs_removed = _sink_params(
            cast("torch.nn.Module", submodule),
            inputs_to_state,
            scope + [name],
            module_id_to_inputs_removed,
        )
        for k, v in submod_id_to_inputs_removed.items():
            module_id_to_inputs_removed[k].update(v)

    graph = getattr(module, "graph", None)
    if graph is None or len(graph.nodes) == 0:
        # Not all modules have graphs defined, if they are empty modules with no operations (like ParameterList)
        return module_id_to_inputs_removed

    if not isinstance(graph, torch.fx.Graph):
        raise AssertionError(f"expected graph to be torch.fx.Graph, got {type(graph)}")

    inputs = list(filter(lambda n: n.op == "placeholder", graph.nodes))
    the_last_input = None if len(inputs) == 0 else inputs[-1]

    # Also remove from call_module nodes
    call_module_nodes = filter(lambda n: n.op == "call_module", graph.nodes)
    for node in call_module_nodes:
        submodule = _get_attr(module, node.target)
        # remove placeholder from call_module node arguments, only if we've
        # erased the placeholder node in the corresponding _sink_params() call
        if submodule is not None and id(submodule) in module_id_to_inputs_removed:
            node.args = tuple(
                filter(
                    lambda n: n.name not in module_id_to_inputs_removed[id(submodule)],
                    node.args,
                )
            )

    # Filter out inputs_to_state corresponding to current scope.
    inputs_to_state_of_scope: dict[torch.fx.Node, list[str]] = {}
    for node in inputs:
        if node.name not in inputs_to_state:
            continue

        state_name = None
        for sn in inputs_to_state[node.name]:
            sn_split = sn.split(".")
            if sn_split[: len(scope)] == [x.split("@")[0] for x in scope]:
                state_name = sn_split
                break

        # If there's a mismatch between scope name and state name, then
        # there must be multiple scopes pointing to the same state name,
        # meaning some modules are shared. In such case, we can simply skip
        # updating the current node because another later iteration will
        # take care of this input node when the unique match between scope
        # and state name occurs.  To make sure this always happen, we should
        # enforce the invariant that no placeholder node in the unflattened
        # graph appears in inputs_to_state dict, which means all the extra
        # input nodes have been handled.
        if state_name is None:
            continue

        inputs_to_state_of_scope[node] = state_name

    # Record name of remove inputs for return purpose.
    inputs_removed: set[str] = set()

    for node, state_name in inputs_to_state_of_scope.items():
        if len(node.users) > 0:
            attr_path = state_name[len(scope) :]
            state_attr = _get_attr_via_attr_list(module, attr_path)
            if not isinstance(state_attr, (torch.Tensor, torch.ScriptObject)):
                raise AssertionError(
                    f"expected state_attr to be torch.Tensor or torch.ScriptObject, got {type(state_attr)}"
                )

            # Make sure the newly created get_attr node is placed after the last placeholder node
            with graph.inserting_after(the_last_input):
                new_node = graph.create_node("get_attr", ".".join(attr_path))

            node.replace_all_uses_with(new_node, propagate_meta=True)

        graph.erase_node(node)
        inputs_removed.add(node.name)

    if isinstance(module, InterpreterModule):
        module.finalize()

    return {id(module): inputs_removed}
def create_add_loggers_graph(
    model: GraphModule,
    subgraphs_dedup: dict[str, list[Node]],
    qconfig_mapping: QConfigMapping,
    node_name_to_qconfig: dict[str, QConfigAny],
) -> None:
    r"""
    Given a model, a model graph partition (currently a set of matched
    subgraphs) and instructions how to transform each subgraph
    (currently quantizing it according to qconfig_mapping), modifies
    the model graph to create an alternate path through the original graph,
    with each of the subgraphs quantized.  This is useful to compare
    propagation error of a transformation such as quantization.

    For example, given layer op0 and op1, there are four cases when handling op1:
    1. op0 and op1 quantized
    2. op0 and op1 unquantized
    3. op0 quantized, op1 unquantized
    4. op0 unquantized, op1 quantized

    Example input, case 1:

    .. code::

      x0_0 -> op0_0 -> x1_0 -> log -----> op1_0 -> x2_0 -> log
       \                        \          \                 \       # noqa: W605
         ---> op0_1 -> x1_1 ----> clog    op1_1 -> x2_1 ----> clog

    Example output, case 1:

    .. code::

      x0_0 -> op0_0 -> x1_0 -> log -----> op1_0 -> x2_0 -> log
       \                        \                           \        # noqa: W605
         ---> op0_1 -> x1_1 ----> clog -> op1_1 -> x2_1 ----> clog

    """
    # TODO(future PR): move logger classes to utils to remove circular dependency
    from torch.ao.ns._numeric_suite_fx import OutputComparisonLogger, OutputLogger

    def _get_subgraph_containing_node(node, subgraphs_dedup):
        for subgraph in subgraphs_dedup.values():
            if node in subgraph:
                return subgraph
        return None

    # First, we need to create shadow branches, going from
    #
    #   x0 -> op0 -> x1 -> ...
    #
    #
    # to
    #
    #   x0 -> op0_0 -> x1_0 -> log -> ...
    #    \                     \
    #      -> op0_1 -> x1_1 -> clog
    #
    # Later, the outputs of each shadow will be rerouted to calculate
    # propagation error.

    # Note: we cannot iterate over matched subgraphs because some nodes
    # may not be matched. So, we iterate over nodes in the graph, and
    # associate them to matched subgraphs if possible.

    nodes_to_skip = set()
    # for each subgraph, save a mapping from first node of subgraph
    # to first and last node of the shadow of this subgraph
    orig_first_node_to_shadow_in_node = {}
    orig_first_node_to_shadow_out_node = {}
    # need to record original list because we will mutate the graph as we go
    orig_nodes = list(model.graph.nodes)  # type: ignore[union-attr, arg-type]
    cur_subgraph_idx = 0
    for n in orig_nodes:
        if n.op in ("placeholder", "get_attr", "output") or n in nodes_to_skip:
            continue

        maybe_subgraph = _get_subgraph_containing_node(n, subgraphs_dedup)
        insert_submodule_copy = False
        if maybe_subgraph is not None:
            first_node, last_node = maybe_subgraph[0], maybe_subgraph[-1]
            nodes_to_skip.update(maybe_subgraph)
            qconfig = node_name_to_qconfig[first_node.name]
            if qconfig is not None:
                insert_submodule_copy = True
        else:
            first_node, last_node = n, n

        if insert_submodule_copy:
            match_name = first_node.name
            create_n_transformed_and_logged_copies_of_subgraph(
                model,
                cur_subgraph_idx,
                match_name,
                maybe_subgraph,
                [qconfig_mapping],
                [node_name_to_qconfig],
                None,
                None,  # type: ignore[arg-type]
            )
            # find the created shadow module and record it so we
            # can find it easily in step 2
            expected_shadow_target = f"shadow_wrapper_{cur_subgraph_idx}_1"
            new_shadow_mod = None
            for maybe_shadow_mod in model.graph.nodes:
                if (
                    maybe_shadow_mod.op == "call_module"
                    and maybe_shadow_mod.target == expected_shadow_target
                ):
                    new_shadow_mod = maybe_shadow_mod
                    break
            if new_shadow_mod is None:
                raise AssertionError("Expected new_shadow_mod to be non-None")
            orig_first_node_to_shadow_in_node[first_node] = new_shadow_mod
            orig_first_node_to_shadow_out_node[first_node] = new_shadow_mod

        else:
            # create a copy of the subgraph by only copying FX nodes
            # but not copying any parameters, to minimize memory usage
            subgraph_to_use = (
                maybe_subgraph if maybe_subgraph is not None else [first_node]
            )

            # add a regular logger after last_node
            qconfig_str = ""
            subgraph_candidate_idx = 0
            fqn = _maybe_get_fqn(first_node, model)
            logger_mod_orig = _get_logger_for_subgraph(
                model,
                first_node,
                last_node,
                cur_subgraph_idx,
                subgraph_candidate_idx,
                qconfig_str,
                OutputLogger,
                fqn,
            )
            attr_name = _get_attr_name(cur_subgraph_idx, subgraph_candidate_idx)
            if hasattr(model, attr_name):
                raise AssertionError(
                    f"Unexpected attribute '{attr_name}' found in {model}"
                )
            setattr(model, attr_name, logger_mod_orig)
            insertion_point = last_node
            with model.graph.inserting_after(insertion_point):
                logger = model.graph.call_module(
                    attr_name, args=(last_node,), kwargs={}
                )
                insertion_point = logger

            # create a copy of the subgraph
            cur_node_orig = first_node
            cur_node_copy = None
            first_node_copy = None
            # pyrefly: ignore [bad-assignment]
            while cur_node_orig in subgraph_to_use:
                # TODO(future PR): make this support all possible args/kwargs
                if cur_node_orig is first_node:
                    new_args = cur_node_orig.args
                    new_kwargs = cur_node_orig.kwargs
                else:
                    first_arg_for_copy: Node | None = cur_node_copy
                    new_args = (first_arg_for_copy, *cur_node_orig.args[1:])
                    new_kwargs = cur_node_orig.kwargs
                # make a copy of cur_node_orig
                with model.graph.inserting_after(insertion_point):
                    cur_node_copy = model.graph.create_node(
                        cur_node_orig.op,
                        cur_node_orig.target,
                        new_args,
                        new_kwargs,
                        # cur_node_orig.name,  # TODO(future PR): set name explicitly
                    )
                    if first_node_copy is None:
                        first_node_copy = cur_node_copy
                # since now only linear subgraphs are supported, all nodes
                # except the last one must have only one user
                if cur_node_orig != last_node:
                    if len(cur_node_orig.users.keys()) != 1:
                        raise AssertionError(
                            f"Expected exactly 1, but got {len(cur_node_orig.users)}"
                        )
                cur_node_orig = next(iter(cur_node_orig.users.keys()))
                if cur_node_orig.name.startswith(SHADOW_NODE_NAME_PREFIX):
                    raise AssertionError(
                        "cur_node_orig should not start with SHADOW_NODE_NAME_PREFIX"
                    )
                insertion_point = cur_node_copy

            # add a comparison logger after last_node's copy
            subgraph_candidate_idx = 1
            logger_mod_orig = _get_logger_for_subgraph(
                model,
                first_node,
                last_node,
                cur_subgraph_idx,
                subgraph_candidate_idx,
                qconfig_str,
                OutputComparisonLogger,
                fqn,
            )
            attr_name = _get_attr_name(cur_subgraph_idx, subgraph_candidate_idx)
            if hasattr(model, attr_name):
                raise AssertionError(
                    f"Unexpected attribute '{attr_name}' found in {model}"
                )
            setattr(model, attr_name, logger_mod_orig)
            with model.graph.inserting_after(insertion_point):
                logger = model.graph.call_module(
                    attr_name, args=(cur_node_copy, last_node), kwargs={}
                )

            # save the final node so we can use it in step 2
            orig_first_node_to_shadow_in_node[first_node] = first_node_copy
            orig_first_node_to_shadow_out_node[first_node] = cur_node_copy

        cur_subgraph_idx += 1

    model.recompile()

    # Now, we go from
    #
    #   x0 -> op0_0 -> x1_0 -> log -> x1 -> op1_0 -> ...
    #    \                     \       \
    #      -> op0_1 -> x1_1 -> clog      -> op1_1 -> ...
    #
    # to
    #
    #   x0 -> op0_0 -> x1_0 -> log --> x1_0 -> op1_0 -> ...
    #    \                     \
    #      -> op0_1 -> x1_1 -> clog -> x1_1 -> op1_1 -> ...
    #
    # sample values of key internal variables for the example above:
    #
    #   orig_first_node_to_shadow_in_node = {op0_0: op0_1, op1_0: op1_1}
    #   orig_first_node_to_shadow_out_node = {op0_0: op0_1, op1_0: op1_1}
    #
    # note: for subgraphs with more than one node, in_node will be different
    # compared to out_node

    nodes_to_skip = set()
    for n in orig_nodes:
        if n.op in ("placeholder", "get_attr", "output") or n in nodes_to_skip:
            continue

        maybe_subgraph = _get_subgraph_containing_node(n, subgraphs_dedup)
        if maybe_subgraph is not None:
            first_node, last_node = maybe_subgraph[0], maybe_subgraph[-1]
            nodes_to_skip.update(maybe_subgraph)
        else:
            first_node, last_node = n, n

        def maybe_remap_node_to_shadow(node):
            """
            If unshadowed `node` has a shadow version, return that. If not,
            return `node`.
            """
            if not isinstance(node, Node):
                # handle scalars
                return node

            if node.op in ("placeholder", "get_attr"):
                return node

            # Find the shadowed version of this arg from the previous
            # subgraph. For this, we need to:
            # 1. navigate to the first node of the previous subgraph
            # 2. get the output of the shadow wrapper which has (1) as an input

            # For now, assume the arg is in matched subgraphs. In the
            # future we may have to handle the case where this is not true.
            prev_subgraph = _get_subgraph_containing_node(node, subgraphs_dedup)
            if prev_subgraph is None:
                prev_subgraph = [node]
            prev_first_node = prev_subgraph[0]
            prev_shadow_output = orig_first_node_to_shadow_out_node[prev_first_node]
            return prev_shadow_output

        cur_shadow_input = orig_first_node_to_shadow_in_node[first_node]
        if cur_shadow_input is None:
            raise AssertionError("Expected cur_shadow_input to be non-None")
        cur_shadow_input.args = tree_map(
            maybe_remap_node_to_shadow, cur_shadow_input.args
        )
        cur_shadow_input.kwargs = tree_map(
            maybe_remap_node_to_shadow, cur_shadow_input.kwargs
        )

        model.recompile()
def create_a_shadows_b(
    name_a: str,
    gm_a: GraphModule,
    name_b: str,
    gm_b: GraphModule,
    matched_subgraph_pairs: dict[str, tuple[NSSubgraph, NSSubgraph]],
    logger_cls: Callable,
    should_log_inputs: bool,
    node_type_to_io_type_map: dict[str, set[NSNodeTargetType]] | None = None,
) -> GraphModule:
    """
    Creates a new GraphModule consisting of the graph of C, with the meaningful
    nodes of A shadowing the corresponding nodes of B.  For example,

    Graph A:
    a0 -> op0_fp32 -> a1 -> op1_fp32 -> a2

    Graph B:
    b0 -> op0_int8 -> b1 -> op1_int8 -> b2

    matched_node_pairs: {'op0': (op0_fp32, op0_int8), 'op1': (op1_fp32, op1_int8)}

    Graph C (A shadows B):

        / dequant0 -> op0_fp32 -> logger_a_0  / dequant_1 -> op1_fp32 -> logger_a_1
       /                                     /
    b0 -------------> op0_int8 -> logger_b_0 --------------> op1_int8 -> logger_b_1

    In a nutshell, this function does the following for each node pair:
    * copies the necessary attributes and modules from gm_a to gm_b,
      keeping names unique
    * adds a dtype cast op (dequant, quant, etc)
    * adds a copy of node_a in gm_b's graph
    * adds loggers to the outputs of node_a and node_b
    """

    if node_type_to_io_type_map is None:
        node_type_to_io_type_map = get_node_type_to_io_type_map()

    # graph_c is the graph created from copying the nodes of graph_b and inserting
    # the shadows with the nodes copied from graph_a
    graph_c = Graph()
    env_c: dict[str, Any] = {}

    def load_arg(a):
        return map_arg(a, lambda node: env_c[node.name])

    start_node_b_to_matched_subgraph_a_and_name = {}
    end_node_b_to_matched_subgraph_a_and_name = {}
    for match_name, match in matched_subgraph_pairs.items():
        subgraph_a, subgraph_b = match
        ref_node_type_a = get_target_type_str(subgraph_a.base_op_node, gm_a)
        ref_node_type_b = get_target_type_str(subgraph_b.base_op_node, gm_b)
        start_node_b_to_matched_subgraph_a_and_name[subgraph_b.start_node] = (
            subgraph_a,
            match_name,
            ref_node_type_a,
            ref_node_type_b,
        )
        end_node_b_to_matched_subgraph_a_and_name[subgraph_b.end_node] = (
            subgraph_a,
            match_name,
            ref_node_type_a,
            ref_node_type_b,
        )

    for node_b in gm_b.graph.nodes:
        if node_b.op == "output":
            graph_c.output(map_arg(node_b.args[0], load_arg))
            continue

        # calculate the flags to determine what to do with this node
        node_b_is_start_node = node_b in start_node_b_to_matched_subgraph_a_and_name
        node_b_is_end_node = node_b in end_node_b_to_matched_subgraph_a_and_name

        if node_b_is_start_node or node_b_is_end_node:
            if node_b_is_start_node:
                (
                    subgraph_a,
                    ref_name,
                    ref_node_type_a,
                    ref_node_type_b,
                ) = start_node_b_to_matched_subgraph_a_and_name[node_b]
            else:
                if not node_b_is_end_node:
                    raise AssertionError("Expected node_b_is_end_node to be not false")
                (
                    subgraph_a,
                    ref_name,
                    ref_node_type_a,
                    ref_node_type_b,
                ) = end_node_b_to_matched_subgraph_a_and_name[node_b]

            all_op_types_support_shadowing = op_type_supports_shadowing(
                subgraph_a.start_node
            ) and op_type_supports_shadowing(node_b)
            if not all_op_types_support_shadowing:
                print(
                    f"skipping shadow loggers for node_b: {get_target_type_str(node_b, gm_b)}"
                    + f", start_node_a: {get_target_type_str(subgraph_a.start_node, gm_a)}"
                    + ", unsupported"
                )
                env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)
                continue

            # For both start_node and end_node verify that we know how to do
            # the dtype cast. If we do not, skip.
            (
                node_input_type_a,
                node_output_type_a,
            ) = get_node_first_input_and_output_type(
                subgraph_a.start_node, gm_a, logger_cls, node_type_to_io_type_map
            )
            (
                node_input_type_b,
                node_output_type_b,
            ) = get_node_first_input_and_output_type(
                node_b, gm_b, logger_cls, node_type_to_io_type_map
            )
            node_io_types_known_a_and_b = (
                node_input_type_a != NodeInputOrOutputType.UNKNOWN
                and node_output_type_a != NodeInputOrOutputType.UNKNOWN
                and node_input_type_b != NodeInputOrOutputType.UNKNOWN
                and node_output_type_b != NodeInputOrOutputType.UNKNOWN
            )
            if not node_io_types_known_a_and_b:
                print(
                    f"skipping shadow loggers for node_b: {get_target_type_str(node_b, gm_b)}"
                    + f", start_node_a: {get_target_type_str(subgraph_a.start_node, gm_a)}"
                    + ", unknown dtype cast"
                )
                env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)
                continue

            # If we are shadowing from fp32 to int8, we need to insert
            # quantize_per_tensor call with qparams from the previous node.
            # Only do this if we are able to infer these qparams from the graph.
            if (
                node_input_type_a == NodeInputOrOutputType.INT8
                and node_input_type_b == NodeInputOrOutputType.FP32
            ):
                node_a_input_qparams = get_node_input_qparams(
                    subgraph_a.start_node, gm_a, node_type_to_io_type_map
                )
                if not node_a_input_qparams:
                    print(
                        f"skipping shadow loggers for node_b: {get_target_type_str(node_b, gm_b)}"
                        + f", start_node_a: {get_target_type_str(subgraph_a.start_node, gm_a)}"
                        + ", unknown input qparams"
                    )
                    env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)
                    continue

            num_non_param_args_node_a = get_number_of_non_param_args(
                subgraph_a.start_node, gm_a
            )
            if not _can_insert_copy_of_subgraph_a(
                subgraph_a, gm_a, num_non_param_args_node_a
            ):
                print(
                    f"skipping shadow loggers for node_b: {get_target_type_str(node_b, gm_b)}"
                    + f", start_node_a: {get_target_type_str(subgraph_a.start_node, gm_a)}"
                    + ", unhandled logic in subgraph copy"
                )
                env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)
                continue

            fqn_base_a = _maybe_get_fqn(subgraph_a.base_op_node, gm_a)
            fqn_base_b = _maybe_get_fqn(subgraph_b.base_op_node, gm_b)  # type: ignore[possibly-undefined]

            if node_b_is_start_node:
                # if necessary, log the input of node_c
                if should_log_inputs:
                    prev_node_b = get_normalized_nth_input(node_b, gm_b, 0)
                    if isinstance(prev_node_b, Node):
                        prev_node_c = env_c[prev_node_b.name]
                        env_c[prev_node_c.name] = _insert_logger_after_node(
                            prev_node_c,
                            gm_b,
                            logger_cls,
                            "_ns_logger_b_inp_",
                            node_b.name,
                            name_b,
                            ref_name,
                            ref_node_type_b,
                            NSSingleResultValuesType.NODE_INPUT.value,
                            index_within_arg=0,
                            index_of_arg=0,
                            fqn=fqn_base_b,
                        )
                    elif isinstance(prev_node_b, list):
                        # first, save the prev_node instances, because they
                        # will be overwritten in the env after the first logger
                        # is added
                        prev_node_c_list = [env_c[arg.name] for arg in prev_node_b]

                        for arg_idx, prev_node_c in enumerate(prev_node_c_list):
                            env_c[prev_node_c.name] = _insert_logger_after_node(
                                prev_node_c,
                                gm_b,
                                logger_cls,
                                "_ns_logger_b_inp_",
                                node_b.name,
                                name_b,
                                ref_name,
                                ref_node_type_b,
                                NSSingleResultValuesType.NODE_INPUT.value,
                                index_within_arg=arg_idx,
                                index_of_arg=0,
                                fqn=fqn_base_b,
                            )
                    else:
                        # logging of inputs which are not lists is not supported yet
                        raise AssertionError(
                            f"type {type(prev_node_b)} is not handled yet"
                        )
                # subgraph so far:
                #
                # (prev_node_c)+ -> (logger_c_input)?

            # Note: this if statement is always True, spelling it out to clarify code
            # intent.
            if node_b_is_start_node or node_b_is_end_node:
                # ensure env_c is populated with base node
                env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)
                node_c = env_c[node_b.name]

                # after this point,
                #
                # node_a is the original node from graph_a, with parent module gm_a
                # node_b is the original node from graph_b, with parent module gm_b
                # node_c is the copy of node_b in graph_c
                #
                # subgraph so far:
                #
                # (prev_node_c)+ -> (logger_c_input)? -> node_start_c

            if node_b_is_start_node:
                # cast dtype from the dtype of node_c's input to the dtype of
                # node_a's input (dequant, etc)
                # prev_node_c = node_c.args[0]
                prev_node_c = get_normalized_nth_input(node_c, gm_b, 0)  # type: ignore[possibly-undefined]
                if should_log_inputs:
                    # skip the input logger when inserting a dtype cast
                    if isinstance(prev_node_c, Node):
                        # pyrefly: ignore [unbound-name]
                        prev_node_c = get_normalized_nth_input(node_c, gm_b, 0)
                    elif isinstance(prev_node_c, list):
                        prev_node_c = [
                            get_normalized_nth_input(arg, gm_b, 0)
                            for arg in prev_node_c
                        ]
                dtype_cast_node = _insert_dtype_cast_after_node(
                    subgraph_a.start_node,
                    # pyrefly: ignore [unbound-name]
                    node_c,
                    prev_node_c,
                    gm_a,
                    gm_b,
                    graph_c,
                    node_b.name + "_dtype_cast_",
                    logger_cls,
                    node_type_to_io_type_map,
                )
                # note: not inserting to env_c because all nodes which use the dtype
                #   casts are copied from graph_a
                #
                # subgraph so far:
                #
                #           (dtype_cast_node)+
                #                  /
                # (prev_node_c)+ -> (logger_c_input)? -> node_start_c

                # if input logging is enabled, log the input to the subgraph
                if should_log_inputs:
                    # TODO: explain this
                    ref_node_name = ""
                    if isinstance(dtype_cast_node, Node):
                        dtype_cast_node = _insert_logger_after_node(
                            dtype_cast_node,
                            gm_b,
                            logger_cls,
                            "_ns_logger_a_inp_",
                            ref_node_name,
                            name_a,
                            ref_name,
                            ref_node_type_a,
                            NSSingleResultValuesType.NODE_INPUT.value,
                            index_within_arg=0,
                            index_of_arg=0,
                            fqn=fqn_base_a,
                        )
                        input_logger: Node | list[Node] = dtype_cast_node
                    else:
                        if not isinstance(dtype_cast_node, list):
                            raise AssertionError(
                                f"Expected list, got {type(dtype_cast_node)}"
                            )
                        new_loggers = []
                        for dtype_cast_idx, dtype_cast_node_inner in enumerate(
                            dtype_cast_node
                        ):
                            dtype_cast_logger = _insert_logger_after_node(
                                dtype_cast_node_inner,
                                gm_b,
                                logger_cls,
                                "_ns_logger_a_inp_",
                                ref_node_name,
                                name_a,
                                ref_name,
                                ref_node_type_a,
                                NSSingleResultValuesType.NODE_INPUT.value,
                                index_within_arg=dtype_cast_idx,
                                index_of_arg=0,
                                fqn=fqn_base_a,
                            )
                            new_loggers.append(dtype_cast_logger)
                        dtype_cast_node = new_loggers
                        input_logger = dtype_cast_node
                    # subgraph so far:
                    #
                    #       (dtype_cast_node)+ -> (logger_a_input)?
                    #                  /
                    # prev_node_c -> (logger_c_input)? -> node_start_c

                # hook up the new mod_a copy to be in the graph, receiving the
                # same inputs as mod_b does, with dtype cast to match a
                # Some ops, such as LSTMs, have two non-param inputs. If we have
                # such an op, pass the second param as well. Note: dtype casting
                # for the second param is not implemented yet, it can be added
                # later if there is a use case.
                node_c_second_non_param_arg = None
                num_non_param_args_node_a = get_number_of_non_param_args(
                    subgraph_a.start_node, gm_a
                )
                if num_non_param_args_node_a == 2:
                    # node_c_second_non_param_arg = node_c.args[1]
                    node_c_second_non_param_arg = get_normalized_nth_input(
                        # pyrefly: ignore [unbound-name]
                        node_c,
                        gm_b,
                        1,
                    )
                node_a_shadows_c = _insert_copy_of_subgraph_a_after_input_node_c(
                    dtype_cast_node,
                    node_c_second_non_param_arg,
                    subgraph_a,
                    gm_a,
                    gm_b,
                    # pyrefly: ignore [unbound-name]
                    node_c.name + "_shadow_copy_",
                )
                env_c[node_a_shadows_c.name] = node_a_shadows_c
                # subgraph so far:
                #
                #       dtype_cast_node -> (logger_a_input)? -> subgraph_a_copy(args/kwargs not shown)
                #                  /
                # (prev_node_c)+ -> (logger_c_input)? -> node_start_c

                if should_log_inputs:
                    # When we created the input logger, we left the ref_node_name
                    # as an empty string, because the subgraph copy did not exist
                    # yet. Now that the subgraph copy exists, we modify this name
                    # to its true value.
                    # Note: the alternative to this is to create the input logger
                    # after creating the subgraph, which is slightly more
                    # complicated. This is the lesser of two evils.
                    # input_logger = env_c[dtype_cast_node.name]
                    # Find the first node in the subgraph
                    cur_node = node_a_shadows_c
                    while get_normalized_nth_input(cur_node, gm_b, 0) != input_logger:  # type: ignore[possibly-undefined]
                        cur_node = get_normalized_nth_input(cur_node, gm_b, 0)  # type: ignore[assignment]
                    # pyrefly: ignore [unbound-name]
                    if isinstance(input_logger, Node):
                        # pyrefly: ignore [unbound-name]
                        input_logger_mod = getattr(gm_b, input_logger.name)
                        input_logger_mod.ref_node_name = cur_node.name
                    else:
                        # pyrefly: ignore [unbound-name]
                        if not isinstance(input_logger, list):
                            raise AssertionError(
                                # pyrefly: ignore [unbound-name]
                                f"Expected list, got {type(input_logger)}"
                            )
                        # pyrefly: ignore [unbound-name]
                        for input_logger_inner in input_logger:
                            input_logger_mod = getattr(gm_b, input_logger_inner.name)
                            input_logger_mod.ref_node_name = cur_node.name

                # hook up a logger to the mod_a copy
                env_c[node_a_shadows_c.name] = _insert_logger_after_node(
                    env_c[node_a_shadows_c.name],
                    gm_b,
                    logger_cls,
                    "_ns_logger_a_",
                    node_a_shadows_c.name,
                    name_a,
                    ref_name,
                    ref_node_type_a,
                    NSSingleResultValuesType.NODE_OUTPUT.value,
                    index_within_arg=0,
                    index_of_arg=0,
                    fqn=fqn_base_a,
                )
                # subgraph so far:
                #
                #       dtype_cast_node -> (logger_a_input)? -> subgraph_a_copy -> logger_a
                #                  /
                # (prev_node_c)+ -> (logger_c_input)? -> node_start_c

            if node_b_is_end_node:
                # hook up a logger to the mod_b copy
                env_c[node_b.name] = _insert_logger_after_node(
                    env_c[node_b.name],
                    gm_b,
                    logger_cls,
                    "_ns_logger_b_",
                    node_b.name,
                    name_b,
                    ref_name,
                    ref_node_type_b,
                    NSSingleResultValuesType.NODE_OUTPUT.value,
                    index_within_arg=0,
                    index_of_arg=0,
                    fqn=fqn_base_b,
                )
                # subgraph so far:
                #
                #       dtype_cast_node -> (logger_a_input)? -> subgraph_a_copy -> logger_a
                #                  /
                # (prev_node_c+) -> (logger_c_input)? -> node_start_c -> ... -> node_end_c -> logger_c
                #
                # Note: node_start_c may be the same node as node_end_c, or they
                # may have nodes in between.

        else:
            env_c[node_b.name] = graph_c.node_copy(node_b, load_arg)

    gm_c = GraphModule(gm_b, graph_c)
    return gm_c
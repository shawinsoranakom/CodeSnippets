def insert_observers_for_model(
    model: GraphModule,
    node_name_to_match_result_with_qconfig: dict[str, _MatchResultWithQConfig],
    node_name_to_qconfig: dict[str, QConfigAny],
    prepare_custom_config: PrepareCustomConfig,
    equalization_config_map: dict[str, Any],
    backend_config: BackendConfig,
    observed_node_names: set[str],
    is_qat: bool,
) -> Node | None:
    """
    Inserts observers, using the following high level algorithm:

    For each node in the graph:
      1. determine the target dtype of this node in the quantized graph, and save
           it for future steps
      2. determine the target dtype or all args and kwargs of this node
      3. if any arg or kwarg's target dtype does not match the current node's
           dtype, insert an observer
      4. if the current node needs an output observer, insert it

    For example:

    - starting graph:
        x0 -> linear -> x1

    - observed graph after processing x0:
        x0(fp32)

    - observed graph after processing linear:
        x0(fp32) -> x0_obs0(int8) -> linear(int8) -> linear_obs0(int8)

    - observed graph after processing x1:
        x0(fp32) -> x0_obs0(int8) -> linear(int8) -> linear_obs0(int8) -> x1

    After a node is processed, the naive observer placement is guaranteed to be
    complete for that node and all of its predecessors. There can be future
    passes which optimize the graph by deduplicating observers, etc.
    """

    # node.meta["target_dtype_info"] stores the target dtype information
    # that's derived from qconfig for the Node, for example, if we have
    # a conv2d node that has a qconfig
    # qconfig = QConfig(activation=..., weight=...)
    # # information for input and bias node omitted
    # # for getattr node
    # # weight = getattr(self, 'weight')
    # weight.meta["target_dtype_info"] = {
    #    'output_act_obs_or_fq_ctr': qconfig.weight,
    # }
    # # for conv2d node
    # # conv2d = call_function[target=torch.nn.functional.conv2d](
    # #            args=(input, weight, bias))
    # conv2d.meta["target_dtype_info"] = {
    #   'input_act_obs_or_fq_ctr': qconfig.activation
    #   'weight_obs_or_fq_ctr': qconfig.weight,
    #   'bias_obs_or_fq_ctr': PlaceholderObserver.with_args(dtype=torch.float32),
    #   'output_act_obs_or_fq_ctr': qconfig.activation,
    # }
    #
    cache_for_no_tensor_check: dict[Node, bool] = {}

    # first, populate the dtype map based only on qconfig and qhandler
    # this assumes:
    # graph inputs are fp32 by default, and int8 where overridden
    # other nodes output dtype is specified by the qconfig
    named_modules = dict(model.named_modules(remove_duplicate=False))

    input_quantized_idxs: list[int] = prepare_custom_config.input_quantized_indexes
    output_quantized_idxs: list[int] = prepare_custom_config.output_quantized_indexes
    processed_nodes: set[Node] = set()
    # initialize target_dtype_info
    for node in model.graph.nodes:
        node.meta["target_dtype_info"] = copy.copy(
            _DEFAULT_FP32_QCONFIG_FOR_TARGET_DTYPE_INFO
        )

    inputs_seen_counter = 0
    outputs_seen_counter = 0
    placeholder_node_to_input_index: dict[Node, int] = {}
    # TODO: we probably don't need this counter since each graph will only have
    # one output node?
    output_node_to_output_index: dict[Node, int] = {}
    for node in model.graph.nodes:
        if node.op == "placeholder":
            placeholder_node_to_input_index[node] = inputs_seen_counter
            inputs_seen_counter += 1
        if node.op == "output":
            output_node_to_output_index[node] = outputs_seen_counter
            outputs_seen_counter += 1

    # Step 1, set the observer or fake quantize module constructor for each node in the
    # matched_node_pattern

    for match_res_with_qconfig in node_name_to_match_result_with_qconfig.values():
        (
            last_node,
            matched_node_pattern,
            pattern,
            qhandler,
            qconfig,
        ) = match_res_with_qconfig
        if qhandler is None:
            raise AssertionError("qhandler must not be None")
        _set_target_dtype_info_for_matched_node_pattern(
            matched_node_pattern,
            last_node,
            qconfig,
            qhandler,
            backend_config,
            named_modules,
            cache_for_no_tensor_check,
            processed_nodes,
        )

    # Step 2. Special cases for some operators, we might be able to remove them
    # in the future if we know dtype information of each node better

    # Step 2.1. some settings are not based on patterns, we need to process each node
    # instead
    for node in model.graph.nodes:
        if (
            node.op == "placeholder"
            and placeholder_node_to_input_index[node] in input_quantized_idxs
        ):
            # users are not supposed to call calculate_qparams on PlaceholderObserver, and
            # this is OK because we are using this as a way to encode the dtypes of input
            # tensor, we won't actually insert these observers in the graph and won't
            # actually call calculate_qparams
            node.meta["target_dtype_info"] = copy.copy(
                _DEFAULT_QUINT8_QCONFIG_FOR_TARGET_DTYPE_INFO
            )
        elif node.op in ("call_module", "call_method", "call_function"):
            args_have_no_tensors = all_node_args_have_no_tensors(
                node, named_modules, cache_for_no_tensor_check
            )
            if args_have_no_tensors:
                node.meta["target_dtype_info"] = {
                    "input_act_obs_or_fq_ctr": None,
                    "output_act_obs_or_fq_ctr": None,
                }
        elif (
            node.op == "output"
            and output_node_to_output_index[node] in output_quantized_idxs
        ):
            # TODO(future PR): update the output_quantized_idxs API to match
            # arbitrary data structures. There is always a single output, and
            # that output can have arbitrary nesting of values. List[int] is
            # not the right data type for this.

            # TODO(future PR): support more dtypes in model outputs, if necessary
            node.meta["target_dtype_info"] = copy.copy(
                _DEFAULT_QUINT8_QCONFIG_FOR_TARGET_DTYPE_INFO
            )

    # Step 2.2, for nodes with known input dtypes, propagate them throughout the
    # graph. For example, if there is a call such as
    #   x1 = x0.masked_fill(mask, 1)
    # we propagate the type of mask to be torch.bool
    propagate_dtypes_for_known_nodes(
        model.graph, node_name_to_match_result_with_qconfig
    )

    # Step 3, check if the requested target_dtype_info is supported by backend or not
    # if not, we'll reset the target_dtye_info to use the default (float Tensor)

    # reset the counters and set of processed_nodes
    processed_nodes: set[Node] = set()
    for match_res_with_qconfig in node_name_to_match_result_with_qconfig.values():
        (
            last_node,
            matched_node_pattern,
            pattern,
            qhandler,
            qconfig,
        ) = match_res_with_qconfig
        is_supported_by_backend = (
            _is_pattern_dtype_config_and_qconfig_supported_by_backend(
                pattern, matched_node_pattern, qconfig, backend_config
            )
        )
        if qhandler is None:
            raise AssertionError("qhandler must not be None")

        # get output_act_dtype so that we don't also reset the special typed nodes
        # TODO: we might want to handle these more uniformly with the default path
        # this can be improved if we can use node.meta["val"]
        output_act_or_fq_ctr = node.meta["target_dtype_info"][
            "output_act_obs_or_fq_ctr"
        ]
        output_act_or_fq = output_act_or_fq_ctr() if output_act_or_fq_ctr else None
        output_act_dtype, _ = _get_dtype_and_is_dynamic(output_act_or_fq)
        if not is_supported_by_backend and output_act_dtype not in [
            None,
            int,
            float,
            torch.bool,
        ]:
            # restore target_dtype_info to default if it is not supported by backend
            _set_target_dtype_info_for_matched_node_pattern(
                matched_node_pattern,
                last_node,
                torch.ao.quantization.qconfig._default_fp32_placeholder_qconfig,
                None,
                backend_config,
                named_modules,
                cache_for_no_tensor_check,
                processed_nodes,
            )

    # After this point, the current node and all of its arguments
    # have a target_dtype_info assigned. Now, we insert observers for inputs
    # of this node (if needed for this node), and the output of this node
    # (if needed for this node).

    # Since we are mutating the graph as we go, we iterate over the original
    # nodes before observer insertion, instead of model.graph.nodes.
    nodes_before_observation = list(model.graph.nodes)

    # Avoid duplicates custom module swaps for multiple nodes with same target.
    custom_module_names_already_swapped: set[str] = set()

    # TODO: reuse placeholder_node_to_input_index and output_node_to_output_index
    # reset inputs/outputs counters
    inputs_seen_counter = 0
    outputs_seen_counter = 0
    results_node = None
    obs_or_fq_map: dict[EdgeOrNode, ObserverOrFakeQuantize] = {}
    model_device = assert_and_get_unique_device(model)

    # TODO: change this to insert obs/fq by pattern instead of by node
    for node in nodes_before_observation:
        if node.op == "placeholder":
            # if a graph input is in fp32, it does not need observation
            # if a graph input is in int8, we assume the observation happens
            #   outside of the graph, and no additional observation is needed
            pass

        elif node.op in ("call_module", "call_method", "call_function", "output"):
            # check for matches
            (
                last_node,
                matched_node_pattern,
                pattern,
                qhandler,
                qconfig,
            ) = node_name_to_match_result_with_qconfig.get(  # type: ignore[assignment]
                node.name, (None, None, None, None, None)
            )
            equalization_qconfig = equalization_config_map.get(node.name)

            this_node_dtype_info = node.meta["target_dtype_info"]
            if "val" in node.meta:
                output_is_a_tensor = this_node_dtype_info is not None and isinstance(
                    node.meta["val"], FakeTensor
                )
            else:
                output_is_a_tensor = this_node_dtype_info is not None

            skip_inserting_observers = (
                (qconfig is None) or not output_is_a_tensor
            ) and (node.op != "output")

            # TODO: take a closer look to see if we can remove this check
            # right now it is here because of `observed_node_names`, we are using
            # it as an indicator for swapping the modules to reference modules in
            # convert
            is_supported_by_backend = (
                _is_pattern_dtype_config_and_qconfig_supported_by_backend(
                    pattern, matched_node_pattern, qconfig, backend_config
                )
            )

            if not skip_inserting_observers and is_supported_by_backend:
                named_modules = dict(model.named_modules(remove_duplicate=False))
                if node.op != "output":
                    if matched_node_pattern is None:
                        raise AssertionError("matched_node_pattern must not be None")
                    # add matched nodes to the observed node name set
                    _add_matched_node_name_to_set(
                        matched_node_pattern, observed_node_names
                    )

                    # This is currently only used for equalization.
                    # Checks if the current node is in a branch in which the two
                    # first layers are both being quantized.
                    #
                    # ex.       conv2
                    #         /
                    #      x -> conv1
                    #
                    # If this is the case, we will not apply equalization to the
                    # initial two layers.
                    is_quantized_branch = False
                    if (
                        len(node.args) > 0
                        and isinstance(node.args[0], Node)
                        and len(node.args[0].users) > 1
                    ):
                        for user in node.args[0].users:
                            # Checks if there exists another user being quantized
                            is_user_quantized = node_name_to_qconfig.get(
                                user.name
                            ) is not None or (
                                user.op == "call_module"
                                and isinstance(
                                    named_modules[str(user.target)], ObserverBase
                                )
                            )
                            if user != node and is_user_quantized:
                                is_quantized_branch = True

                    pattern_to_root_node_getter = (
                        get_fusion_pattern_to_root_node_getter(backend_config)
                    )
                    root_node_getter = pattern_to_root_node_getter.get(
                        pattern, _default_root_node_getter
                    )
                    root_node = root_node_getter(matched_node_pattern)
                    is_input_node_of_the_pattern = node is root_node
                    if is_input_node_of_the_pattern:
                        # this modifies node inplace
                        _maybe_insert_input_observers_for_node(
                            node,
                            qconfig,
                            model,
                            named_modules,
                            model.graph,
                            qhandler,
                            prepare_custom_config,
                            obs_or_fq_map,
                            is_qat,
                            backend_config,
                            model_device,
                        )

                        # insert equalization input observers if needed
                        _maybe_insert_input_equalization_observers_for_node(
                            node,
                            equalization_qconfig,
                            model,
                            named_modules,
                            model.graph,
                            is_quantized_branch,
                        )

                    is_last_node_of_pattern = node is last_node
                    input_output_share_observers = node.meta["target_dtype_info"].get(
                        "input_output_share_observers", False
                    )
                    reuse_input_obs_or_fq = node.meta["target_dtype_info"].get(
                        "reuse_input_obs_or_fq", False
                    )

                    if is_last_node_of_pattern:
                        if _is_custom_module_lstm(
                            # pyrefly: ignore [bad-argument-type]
                            node,
                            named_modules,
                            qconfig,
                            qhandler,
                        ):
                            # Currently custom module outputs are assumed to be already quantized,
                            # so we need to insert a DeQuantStub after the output. For custom module
                            # LSTM specifically, the outputs are also a nested tuple, so we must first
                            # break down the tuple to insert DeQuantStubs after the internal nodes.

                            # TODO: This currently diverges from how custom modules are handled today,
                            # where we insert observers after the output instead of DeQuantStubs, and
                            # replace these observers with "dequantize" nodes during convert. Conceptually,
                            # these output observers are the same as DeQuantStubs. In the future, we
                            # should resolve this inconsistency by inserting DeQuantStubs for all custom
                            # modules, not just for LSTM.
                            _insert_dequant_stubs_for_custom_module_lstm_output(
                                # pyrefly: ignore [bad-argument-type]
                                node,
                                model,
                                named_modules,
                                model.graph,
                            )
                            # pyrefly: ignore [missing-attribute]
                            if node.target not in custom_module_names_already_swapped:
                                # pyrefly: ignore [bad-argument-type]
                                custom_module_names_already_swapped.add(node.target)
                                _swap_custom_module_to_observed(
                                    # pyrefly: ignore [bad-argument-type]
                                    node,
                                    qconfig,
                                    named_modules,
                                    prepare_custom_config,
                                )
                        else:
                            # this returns the new observer node if it was needed
                            maybe_output_obs_node = (
                                _maybe_insert_output_observer_for_node(
                                    # pyrefly: ignore [bad-argument-type]
                                    node,
                                    model,
                                    named_modules,
                                    model.graph,
                                    obs_or_fq_map,
                                    is_qat,
                                )
                            )

                            if maybe_output_obs_node is not None:
                                # Update users of original node to use the output observer
                                # instead. For example, change
                                #
                                #           next_node
                                #          /
                                #   cur_node -> obs
                                #
                                # to
                                #
                                #                 next_node
                                #                 /
                                #   cur_node -> obs
                                #
                                # We need to save orig users before updating uses because
                                # the list of users will change as we update uses
                                # pyrefly: ignore [missing-attribute]
                                orig_users = list(node.users.keys())
                                for user_node in orig_users:
                                    if user_node is maybe_output_obs_node:
                                        continue
                                    user_node.replace_input_with(
                                        node, maybe_output_obs_node
                                    )

                                _is_observer_in_same_graph_ = (
                                    _is_observer_in_same_graph(
                                        # pyrefly: ignore [bad-argument-type]
                                        node,
                                        named_modules,
                                        obs_or_fq_map,
                                        is_qat,
                                    )
                                )

                                # for ops whose inputs and outputs share observer/fqs, we modify the graph
                                # to make all inputs and outputs use the first input's
                                # observer/fq
                                if (
                                    input_output_share_observers
                                    and _is_observer_in_same_graph_
                                ) or reuse_input_obs_or_fq:
                                    if not _maybe_make_input_output_share_observers(
                                        # pyrefly: ignore [bad-argument-type]
                                        node,
                                        model,
                                        named_modules,
                                    ):
                                        _remove_output_observer(
                                            # pyrefly: ignore [bad-argument-type]
                                            node,
                                            model,
                                            named_modules,
                                        )

                                if qhandler is not None and qhandler.is_custom_module():
                                    if (
                                        # pyrefly: ignore [missing-attribute]
                                        node.target
                                        not in custom_module_names_already_swapped
                                    ):
                                        custom_module_names_already_swapped.add(
                                            # pyrefly: ignore [bad-argument-type]
                                            node.target
                                        )
                                        _swap_custom_module_to_observed(
                                            # pyrefly: ignore [bad-argument-type]
                                            node,
                                            qconfig,
                                            named_modules,
                                            prepare_custom_config,
                                        )

                else:  # output
                    _maybe_insert_observers_before_graph_output(
                        node, model, named_modules, model.graph, obs_or_fq_map, is_qat
                    )

        #
        # After this point, the current node has input and output observers
        # that it needs for itself inserted.
        #

        # increment the counters, so future inputs and outputs are assigned
        # correct dtypes
        if node.op == "placeholder":
            inputs_seen_counter += 1
        elif node.op == "output":
            outputs_seen_counter += 1
            results_node = node

    return results_node
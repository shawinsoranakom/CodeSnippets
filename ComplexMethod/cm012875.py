def _maybe_insert_input_observer_for_arg_or_kwarg(
    node: Node | Any,
    arg: Argument,
    qconfig: QConfigAny,
    model: torch.nn.Module,
    named_modules: dict[str, torch.nn.Module],
    graph: Graph,
    qhandler: QuantizeHandler | None,
    prepare_custom_config: PrepareCustomConfig,
    obs_or_fq_map: dict[EdgeOrNode, ObserverOrFakeQuantize],
    is_qat: bool,
    backend_config: BackendConfig | None = None,
    model_device: torch.device | None = None,
) -> Argument:
    """
    Given a `node` and an `arg`, inserts an input observer between
    `node` and `arg` if necessary.
    """
    # for ops such as torch.cat([x0, x1]),
    # traverse through the list
    if isinstance(arg, (list, tuple)):
        new_arg_to_return = []
        for inner_arg in arg:
            new_inner_arg = _maybe_insert_input_observer_for_arg_or_kwarg(
                node,
                inner_arg,
                qconfig,
                model,
                named_modules,
                graph,
                qhandler,
                prepare_custom_config,
                obs_or_fq_map,
                is_qat,
                backend_config,
                model_device,
            )
            new_arg_to_return.append(new_inner_arg)
        return type(arg)(new_arg_to_return)

    if not isinstance(arg, Node):
        return arg
    if not isinstance(arg, Node):
        raise AssertionError("arg must be a Node")
    # default (no observer)
    new_arg = arg

    is_standalone_module = qhandler is not None and qhandler.is_standalone_module()
    # TODO: move this to a separate function
    if not is_standalone_module:
        # Note: qconfig can be None in this branch this we are getting act/fq from
        # node.meta now
        # regular flow for most nodes, except standalone modules

        if "quantization_annotation" in node.meta:
            raise NotImplementedError(
                "Please use torchao (https://github.com/pytorch/ao) for pt2e quantization flow"
            )

        if "target_dtype_info" not in node.meta:
            raise AssertionError("expected 'target_dtype_info' in node.meta")
        # TODO: we are assuming "target_dtype_info" exists here, maybe
        # a default value also need to be provided here
        target_dtype_info = node.meta["target_dtype_info"]
        # for nodes that doesn't have `reuse_input_obs_or_fq` configured,
        # we'll default to False, this makes configuring this field optional for users
        reuse_input_obs_or_fq = target_dtype_info.get("reuse_input_obs_or_fq", False)
        arg_as_input_act_obs_or_fq = _get_arg_as_input_act_obs_or_fq(
            arg, node, named_modules, obs_or_fq_map, is_qat
        )
        (
            arg_as_input_target_dtype,
            arg_as_input_target_is_dynamic,
        ) = _get_dtype_and_is_dynamic(arg_as_input_act_obs_or_fq)

        arg_as_output_act_obs_or_fq = _get_output_act_obs_or_fq(
            arg, named_modules, obs_or_fq_map, is_qat
        )
        (
            arg_as_output_target_dtype,
            arg_as_output_target_is_dynamic,
        ) = _get_dtype_and_is_dynamic(arg_as_output_act_obs_or_fq)

        needs_obs_or_fq = _needs_obs_or_fq(
            arg_as_output_target_dtype,
            arg_as_output_target_is_dynamic,
            arg_as_input_target_dtype,
            arg_as_input_target_is_dynamic,
            reuse_input_obs_or_fq,
            is_zeroth_arg=len(node.args) > 0 and arg is node.args[0],
        )

    else:
        if qconfig is None:
            raise AssertionError("qconfig must not be None")
        # custom flow for standalone modules
        _, _, sm_prepare_custom_config, _ = _get_standalone_module_configs(
            node, named_modules, prepare_custom_config, qconfig, backend_config
        )
        sm_input_quantized_idxs = sm_prepare_custom_config.input_quantized_indexes

        # for args, this is set to the index of the current arg
        # for kwargs, this is left at None
        cur_input_idx = None
        for arg_idx, arg_to_check in enumerate(node.args):
            if arg_to_check is arg:
                cur_input_idx = arg_idx
                break

        if cur_input_idx is None:
            needs_obs_or_fq = False
        else:
            arg_as_output_target_dtype = _get_arg_target_dtype_as_output(
                arg, named_modules, obs_or_fq_map, is_qat
            )
            arg_as_input_target_dtype = (
                torch.quint8
                if cur_input_idx in sm_input_quantized_idxs
                else torch.float
            )
            needs_obs_or_fq = (
                arg_as_output_target_dtype != arg_as_input_target_dtype
            ) and (arg_as_input_target_dtype != torch.float)

        act_post_process_ctr = qconfig.activation
        arg_as_input_act_obs_or_fq = (
            act_post_process_ctr() if act_post_process_ctr else None
        )

    if needs_obs_or_fq:
        existing_obs_node = None

        # Before using the new observer, check if an observer
        # of the correct type already exists. If it does, use it.
        # This prevents duplicate observer insertions if a node is
        # used by multiple nodes.
        # TODO: this is looking into how the value is used in the future
        # we should remove this
        # removing this means we insert one observer for each use, even if they
        # have the same dtype, we can have an extra pass that removes the extra observers
        for maybe_obs_node in arg.users:
            if maybe_obs_node.op == "call_module":
                maybe_obs_mod = named_modules[maybe_obs_node.target]  # type: ignore[index]
                if (
                    type(maybe_obs_mod) is type(arg_as_input_act_obs_or_fq)
                    and maybe_obs_mod.dtype == arg_as_input_target_dtype  # type: ignore[possibly-undefined]
                ):
                    arg_as_input_act_obs_or_fq = maybe_obs_mod  # type: ignore[assignment]
                    existing_obs_node = maybe_obs_node
                    break

        if arg_as_input_act_obs_or_fq is None:
            raise AssertionError("arg_as_input_act_obs_or_fq must not be None")
        obs_or_fq_map[(arg, node)] = arg_as_input_act_obs_or_fq
        if existing_obs_node is None:
            new_obs_node = _insert_obs_or_fq(
                arg,
                arg_as_input_act_obs_or_fq,
                model,
                named_modules,
                graph,
                model_device,
            )
            # override this arg to be the observed arg
            new_arg = new_obs_node
        else:
            new_arg = existing_obs_node

    return new_arg
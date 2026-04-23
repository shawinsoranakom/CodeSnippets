def create_one_transformed_and_logged_copy_of_subgraph(
    mt: GraphModule,
    subgraph_idx: int,
    subgraph_candidate_idx: int,
    first_node: Node,
    last_node: Node,
    fqn: str | None,
    list_of_node_name_to_qconfig: list[dict[str, QConfigAny]],
    example_inputs: Any,
    last_added_shadow_node_list: list[Node | None],
    custom_prepare_fn: Callable | None = None,
    custom_prepare_kwargs: dict[str, Any] | None = None,
) -> None:
    """
    Given a subgraph in `mt` and a subgraph candidate idx, inserts the
    subgraph candidate copy and instruments it with loggers.

    If subgraph_candidate_idx is 0, this is the baseline fp32 subgraph and we just
    add a logger to the end.

    If subgraph_candidate_idx is not 0, we create a copy of the subgraph and
    prepare it with `prepare_fx`.
    """

    # TODO(future PR): move logger classes to utils to remove circular dependency
    from torch.ao.ns._numeric_suite_fx import OutputComparisonLogger, OutputLogger

    if subgraph_candidate_idx == 0:
        # idx = 0 is the floating point (original) version of the subgraph
        # We keep the subgraph as is, and add a logger at the end

        qconfig_str = ""
        logger_mod_orig = _get_logger_for_subgraph(
            mt,
            first_node,
            last_node,
            subgraph_idx,
            subgraph_candidate_idx,
            qconfig_str,
            OutputLogger,
            fqn,
        )

        attr_name = _get_attr_name(subgraph_idx, subgraph_candidate_idx)
        if hasattr(mt, attr_name):
            raise AssertionError(f"Unexpected attribute '{attr_name}' found in {mt}")
        setattr(mt, attr_name, logger_mod_orig)
        with mt.graph.inserting_after(last_node):
            new_node = mt.graph.call_module(attr_name, args=(last_node,), kwargs={})
            last_added_shadow_node_list[0] = new_node

    else:
        # idx > 0 means we have a candidate qconfig to try, so we need
        # to make a copy of the subgraph, feed it with the right inputs,
        # and add a logger at the end

        # get the qconfig
        # subtract one because the first candidate is the floating point
        # version of the subgraph
        node_name_to_qconfig = list_of_node_name_to_qconfig[subgraph_candidate_idx - 1]
        qconfig = node_name_to_qconfig[first_node.name]

        # if no quantization is requested, skip
        # TODO(future PR): deduplicate equivalent qconfigs that come from
        #   different qconfig mapping objects
        if qconfig is None:
            return

        qconfig_mapping = QConfigMapping().set_global(qconfig)

        # create a copy of the submodule, wrapped in a separate module
        orig_mod_copy_wrapped = create_submodule_from_subgraph(
            mt, first_node, last_node
        )

        # add a call to prepare_fx on the wrapper module
        if custom_prepare_fn is None:
            orig_mod_copy_wrapped = torch.ao.quantization.quantize_fx.prepare_fx(
                orig_mod_copy_wrapped, qconfig_mapping, example_inputs=example_inputs
            )
        else:
            if custom_prepare_kwargs is None:
                custom_prepare_kwargs = {}
            for kwarg_name in [
                "example_inputs",
                "prepare_custom_config",
                "qconfig_mapping",
            ]:
                if kwarg_name in custom_prepare_kwargs:
                    raise AssertionError(
                        f"cannot specify {kwarg_name} in custom_prepare_kwargs"
                    )
            prepare_kwargs: dict[str, Any] = {
                "example_inputs": example_inputs,
                "qconfig_mapping": qconfig_mapping,
            }
            prepare_kwargs.update(custom_prepare_kwargs)
            orig_mod_copy_wrapped = custom_prepare_fn(
                orig_mod_copy_wrapped, **prepare_kwargs
            )

        # attach the wrapper to the model
        attr_name = _get_attr_wrapper_name(subgraph_idx, subgraph_candidate_idx)
        if hasattr(mt, attr_name):
            raise AssertionError(f"Unexpected attribute '{attr_name}' found in {mt}")
        setattr(mt, attr_name, orig_mod_copy_wrapped)

        # add a call to the wrapper module from the parent graph
        insert_after_node = last_added_shadow_node_list[0]
        with mt.graph.inserting_after(insert_after_node):
            # TODO(future PR): handle fusion patterns where non-first nodes
            # need inputs

            # pass in all node args and kwargs

            new_args = []
            for arg in first_node.args:
                if isinstance(arg, Node):
                    new_args.append(arg)
                elif (
                    isinstance(arg, (list, tuple))
                    and len(arg)
                    and isinstance(arg[0], Node)
                ):
                    new_args.extend(
                        inner_arg for inner_arg in arg if isinstance(inner_arg, Node)
                    )

            new_kwargs = {}
            for name, old_kwarg in first_node.kwargs.items():
                if isinstance(old_kwarg, Node):
                    new_kwargs[name] = old_kwarg
                elif isinstance(old_kwarg, (list, tuple)) and len(old_kwarg):
                    # TODO(future PR): clarify why we are adding kwargs to args
                    new_args.extend(old_kwarg)  # type: ignore[arg-type]

            new_args = tuple(new_args)  # type: ignore[assignment]

            new_node = mt.graph.call_module(attr_name, args=new_args, kwargs=new_kwargs)  # type: ignore[arg-type]

        # add a logger to parent graph to observe the shadow wrapper
        logger_mod_orig = _get_logger_for_subgraph(
            mt,
            first_node,
            last_node,
            subgraph_idx,
            subgraph_candidate_idx,
            str(qconfig),
            OutputComparisonLogger,
            fqn,
        )

        attr_name = _get_attr_name(subgraph_idx, subgraph_candidate_idx)
        if hasattr(mt, attr_name):
            raise AssertionError(f"Unexpected attribute '{attr_name}' found in {mt}")
        setattr(mt, attr_name, logger_mod_orig)
        with mt.graph.inserting_after(new_node):
            logger = mt.graph.call_module(
                attr_name, args=(new_node, last_node), kwargs={}
            )
            last_added_shadow_node_list[0] = logger

    mt.recompile()
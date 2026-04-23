def default_partition(
    joint_module: fx.GraphModule,
    _joint_inputs: Any,
    *,
    num_fwd_outputs: int,
    static_lifetime_input_indices: list[int] | None = None,
    static_lifetime_input_nodes: OrderedSet[fx.Node] | None = None,
) -> tuple[fx.GraphModule, fx.GraphModule]:
    """
    Partitions the :attr:`joint_module` in a manner that closely resembles the
    behavior observed in the original ``.forward()`` and ``.backward()`` of the
    callable, i.e., the resulting forward graph contains those operators that
    are executed in the original ``.forward()`` callable passed to
    :func:`aot_function`.

    The default partitioner collects the operators that are between the forward
    inputs and the forward outputs. This helps in finding the tensors which have
    to be stashed for the backward pass. These stashed tensors become the output
    of the generated forward graph. The remaining operators are then placed in
    the backward graph.

    .. warning::
        This API is experimental and likely to change.

    Args:
        joint_module(fx.GraphModule): The joint forward and backward graph. This
            is the result of AOT Autograd tracing.

    Returns:
        Returns the generated forward and backward Fx graph modules.
    """
    # Respect the original placement of ops rather than rely on dataflow.
    forward_nodes = []
    last_node = None
    for node in joint_module.graph.nodes:
        if _has_tag_is_forward(node) or _is_primal(node) or _is_fwd_seed_offset(node):
            last_node = node
    if last_node is None:
        raise AssertionError("last_node must not be None")
    for node in joint_module.graph.nodes:
        if not _is_tangent(node):
            forward_nodes.append(node)
        if node is last_node:
            break
    forward_node_names = OrderedSet(
        node.name for node in forward_nodes if node.op != "output"
    )
    graph_has_recomputable_ops = has_recomputable_ops(joint_module)
    graph_has_recomputable_rng_ops = has_recomputable_rng_ops(joint_module)
    if graph_has_recomputable_ops:
        if _is_functional_graph(joint_module.graph)[0] is not None:
            # Fall-back to previous behavior to avoid bc-breaking, although can
            # eventually flip the switch to make this a hard error.
            warnings.warn(
                "Trying to unsafely apply AC to a non-functional graph with the "
                "default partitioner. Falling back to min-cut partitioner."
            )
            return min_cut_rematerialization_partition(
                joint_module,
                _joint_inputs,
                num_fwd_outputs=num_fwd_outputs,
                static_lifetime_input_indices=static_lifetime_input_indices,
            )

        joint_module = cleanup_recompute_tags(joint_module, is_default_partition=True)

    if not config.unsafe_allow_optimization_of_collectives:
        force_save_collectives(joint_module)

    force_save_effectful_ops(joint_module)
    force_save_bw_mutation_src(joint_module)

    if static_lifetime_input_indices is None:
        static_lifetime_input_indices = []
    node_info = classify_nodes(
        joint_module, static_lifetime_input_indices, num_fwd_outputs
    )

    saved_values = []
    saved_sym_nodes = []
    saved_opaque_nodes = []

    distributed_enabled = torch.distributed.is_available()

    def is_tensor(node: fx.Node) -> bool:
        return "tensor_meta" in node.meta or isinstance(
            node.meta.get("val"), torch._subclasses.FakeTensor
        )

    def is_multi_output(node: fx.Node) -> bool:
        return (
            all(user.target == operator.getitem for user in node.users)
            and len(node.users) > 0
        )

    def is_impure(node: fx.Node) -> bool:
        # wait tensor is an "impure" op according to DCE's definition of impure
        # (see is_impure in torch/fx/node.py), but it survives past
        # functionalization and can be safely dup'd and reordered under the
        # assumption SPMD.
        return (
            node.is_impure(impure_random=False)
            and node.op
            not in (
                "placeholder",
                "output",
            )
            and (
                not distributed_enabled
                or node.target is not torch.ops._c10d_functional.wait_tensor.default
            )
        )

    for node in joint_module.graph.nodes:
        if node.name not in forward_node_names:
            continue
        if node.op == "get_attr" and node.name in (
            k for k, v in joint_module.named_modules()
        ):
            continue
        if node.target in (
            torch.ops.aten._assert_scalar.default,
            # Profiler record_function ops are technically impure (they set up
            # profiling spans), but they're safe to duplicate during AC recompute.
            # We skip both enter and exit to keep profiling spans balanced.
            torch.ops.profiler._record_function_enter_new.default,
            torch.ops.profiler._record_function_enter.default,
            torch.ops.profiler._record_function_exit.default,
            torch.ops.profiler._record_function_exit._RecordFunction,
        ):
            continue
        if is_sym_node(node):
            # Symints must be kept separate from tensors so that PythonFunction only calls
            # save_for_backward on tensors and stashes symints in autograd .ctx
            saved_sym_nodes.append(node)
            continue
        if is_multi_output(node):
            # Must be ordered before MUST_SAVE tags to avoid saving tuples marked MUST_SAVE.
            continue
        if node.meta.get("recompute") == CheckpointPolicy.MUST_SAVE:
            if is_opaque_node(node):
                saved_opaque_nodes.append(node)
            else:
                saved_values.append(node)
            continue
        if is_impure(node):
            if graph_has_recomputable_ops:
                raise AssertionError(
                    f"Trying to apply AC on a graph with impure op: {node}, {node.target}"
                )
            if is_opaque_node(node):
                saved_opaque_nodes.append(node)
            else:
                saved_values.append(node)
            continue
        if is_opaque_node(node):
            saved_opaque_nodes.append(node)
            continue
        if not is_tensor(node) and node.op == "call_function":
            raise AssertionError(f"Expected {node} to be a tensor")
        backward_usages = [n for n in node.users if n.name not in forward_node_names]
        if all(is_sym_node(n) for n in backward_usages):
            # If we have a tensor in the forward, where only its sizes/strides are needed in the backward,
            # and not the actual tensor data,
            # then it will be a lot cheaper to save only the sizes/strides, and not the actual tensor.
            #
            # Note that saving the tensor could also cause compilation problems:
            # If the user mutated an input in the forward and uses its sizes/strides in the backward,
            # then we would be obligated to clone the input before saving it to appease autograd.
            # (This is how we originally found this bug).
            saved_sym_nodes.extend(backward_usages)
            continue
        if not must_recompute(node):
            saved_values.append(node)

    saved_values = list(dict.fromkeys(saved_values).keys())
    saved_sym_nodes = list(dict.fromkeys(saved_sym_nodes).keys())
    saved_opaque_nodes = list(dict.fromkeys(saved_opaque_nodes).keys())

    if config._sync_decision_cross_ranks:
        saved_values = _sync_decision_cross_ranks(joint_module.graph, saved_values)

    if static_lifetime_input_nodes is None:
        static_lifetime_input_nodes = node_info.static_lifetime_input_nodes
    fw_module, bw_module = _extract_fwd_bwd_modules(
        joint_module,
        saved_values,
        saved_sym_nodes=saved_sym_nodes,
        saved_opaque_nodes=saved_opaque_nodes,
        num_fwd_outputs=num_fwd_outputs,
        static_lifetime_input_nodes=static_lifetime_input_nodes,
    )

    # Run DCE while overriding the definition of is_impure_node
    fw_module.graph.eliminate_dead_code(is_impure_node=is_not_collective)
    bw_module.graph.eliminate_dead_code(is_impure_node=is_not_collective)

    if graph_has_recomputable_ops:
        if graph_has_recomputable_rng_ops:
            fw_module, bw_module = functionalize_rng_ops(
                joint_module, fw_module, bw_module, len(saved_sym_nodes)
            )
        bw_module = reordering_to_mimic_autograd_engine(bw_module)

    # pyrefly: ignore [unbound-name]
    if config.enable_activation_offloading:
        from ._activation_offloading.activation_offloading import (
            enable_activation_offloading,
        )

        enable_activation_offloading(
            fw_module,
            bw_module,
            num_fwd_outputs,
            static_lifetime_input_nodes,
        )

    # raise all getitem ops to as early as possible
    # this is helpful for memory, especially in the case of aot_eager backend
    fw_module = raise_getitems(fw_module)
    bw_module = raise_getitems(bw_module)

    fw_module = thread_graphsafe_rng_from_hops(fw_module, is_backward=False)
    if len(node_info.required_bw_nodes) > 0:
        bw_module = thread_graphsafe_rng_from_hops(bw_module, is_backward=True)

    return fw_module, bw_module
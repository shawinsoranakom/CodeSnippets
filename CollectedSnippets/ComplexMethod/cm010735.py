def _extract_fwd_bwd_modules(
    joint_module: fx.GraphModule,
    saved_values: list[fx.Node],
    saved_sym_nodes: list[fx.Node],
    saved_opaque_nodes: list[fx.Node] | None = None,
    *,
    num_fwd_outputs: int,
    static_lifetime_input_nodes: OrderedSet[fx.Node] | None = None,
    ignore_must_be_in_fw_bw: bool = False,
    omit_aot_autograd_runtime: bool = False,
) -> tuple[fx.GraphModule, fx.GraphModule]:
    """Extract forward and backward graph modules from a joint graph.

    Args:
        ignore_must_be_in_fw_bw: When True, disables forward/backward placement
            enforcement in _extract_graph_with_inputs_outputs. Needed when the
            joint_module is not an original fwd+bwd joint graph (e.g. a backward
            graph being re-partitioned for dI/dW splitting).
        omit_aot_autograd_runtime: When True, skips postprocessing that is
            only needed when the resulting modules will be wrapped in a custom
            autograd.Function (the AOTAutograd path). This includes: tangent input
            handling, version-counter check sorting of saved tensors, opaque object
            (FakeScriptObject) separation, and fp8 activation quantization. Set this
            to True when the fwd/bwd modules will be executed directly without autograd.
    """
    fwd_outputs, bwd_outputs, fwd_outputs_descs, bwd_outputs_descs = (
        _extract_fwd_bwd_outputs(joint_module, num_fwd_outputs=num_fwd_outputs)
    )
    placeholders = joint_module.graph.find_nodes(op="placeholder")
    primal_inputs = [*filter(_is_primal, placeholders)]
    tangent_inputs = (
        [] if omit_aot_autograd_runtime else [*filter(_is_tangent, placeholders)]
    )
    fwd_seed_offset_inputs = [*filter(_is_fwd_seed_offset, placeholders)]
    bwd_seed_offset_inputs = [*filter(_is_bwd_seed_offset, placeholders)]
    backward_state_inputs = [*filter(_is_backward_state, placeholders)]

    if saved_opaque_nodes is None:
        saved_opaque_nodes = []

    bwd_graph = _extract_graph_with_inputs_outputs(
        joint_module.graph,
        saved_sym_nodes
        + saved_opaque_nodes
        + saved_values
        + tangent_inputs
        + bwd_seed_offset_inputs,
        bwd_outputs,
        bwd_outputs_descs,
        "backward",
        ignore_must_be_in_fw_bw=ignore_must_be_in_fw_bw,
    )

    distributed_enabled = torch.distributed.is_available()

    for node in bwd_graph.find_nodes(op="placeholder"):
        # This is to filter out saved values that don't actually end up being used by the backwards pass
        if not node.users:
            _remove_by_name(saved_values, node.name)
            _remove_by_name(saved_sym_nodes, node.name)
            _remove_by_name(saved_opaque_nodes, node.name)
        # wait_tensor is a bit special: if we have a "dead activation" that is not used in the bw,
        # but this dead activation is actually a collective,
        # then the collective will generally by followed by a wait_tensor() call.
        # we need to peak one node further to see if this wait_tensor is dead as well.
        elif distributed_enabled and all(
            n.target is torch.ops._c10d_functional.wait_tensor.default
            and len(n.users) == 0
            for n in node.users
        ):
            _remove_by_name(saved_values, node.name)
            _remove_by_name(saved_sym_nodes, node.name)
            _remove_by_name(saved_opaque_nodes, node.name)
        elif _is_backward_state(node):
            # BackwardState is saved directly
            _remove_by_name(saved_values, node.name)
            if not backward_state_inputs:
                raise AssertionError("backward_state_inputs must not be empty")

    # Now that we have the finalized list of saved values, we need to ensure
    # we propagate all symbols which are referenced by backwards inputs.
    # These are not directly used in the graph but are required for downstream
    # sizevar assignment
    saved_symbols: OrderedSet[sympy.Symbol] = OrderedSet()
    saved_sym_nodes_binding = []
    saved_sym_nodes_derived = []

    # Some symbols may already be bound in the directly saved_sym_nodes,
    # keep track of them so we don't re-bind them
    for node in saved_sym_nodes:
        symbol = is_symbol_binding_fx_node(node)
        if symbol:
            saved_symbols.add(symbol)
            saved_sym_nodes_binding.append(node)
        else:
            saved_sym_nodes_derived.append(node)

    # Now go through all of the prospective backward inputs and track any
    # other symbols we need to bind
    symbol_bindings = find_symbol_binding_fx_nodes(joint_module.graph)
    for node in itertools.chain(saved_sym_nodes_derived, saved_values, tangent_inputs):
        if "val" not in node.meta:
            continue
        new_symbols = free_symbols(node.meta["val"]) - saved_symbols
        # NB: Deterministic order please!
        for s in sorted(new_symbols, key=lambda s: s.name):
            # NB: For well formed graphs, the symbol should always be present,
            # but we also have ways to produce ill-formed graphs, e.g., direct
            # make_fx usages, so don't choke in this case
            if s not in symbol_bindings:
                continue
            saved_sym_nodes_binding.append(symbol_bindings[s])
        saved_symbols |= new_symbols

    # Update saved_sym_nodes that are now reordered to have all bindings at
    # front. This can also be used later on to figure out the position of saved
    # sym nodes in the output of fwd graph.
    saved_sym_nodes.clear()
    saved_sym_nodes.extend(saved_sym_nodes_binding + saved_sym_nodes_derived)

    if not omit_aot_autograd_runtime:
        # See Note [Activations with no version counter checks in eager]
        # Sort saved_values so that tensors with saved_tensor_with_no_vc_check=True
        # are at the end. This allows us to have two consecutive slices:
        # 1. tensors_saved_with_vc_check_slice - tensors saved via save_for_backward
        # 2. tensors_saved_with_no_vc_check_slice - tensors stashed on ctx without save_for_backward
        # The sort is stable, so the relative order within each group is preserved.
        #
        # Additionally, separate out opaque objects (FakeScriptObject) from tensors.
        # Opaque objects should be placed after tensors in the forward outputs.
        saved_values_with_vc_check = []
        saved_values_no_vc_check = []
        saved_opaque_objects = []
        for node in saved_values:
            # Check if this is an opaque object
            if isinstance(node.meta.get("val"), FakeScriptObject):
                saved_opaque_objects.append(node)
            elif node.meta.get("saved_tensor_with_no_vc_check", False):
                saved_values_no_vc_check.append(node)
            else:
                saved_values_with_vc_check.append(node)
        saved_values.clear()
        saved_values.extend(saved_values_with_vc_check + saved_values_no_vc_check)
        no_vc_check_start_idx = len(saved_values_with_vc_check)

        # debug assert: given saved_values where the last k of them are expected to not
        # require VC checks, they should all have node metadata indicating so.
        for i, node in enumerate(saved_values):
            if i >= no_vc_check_start_idx:
                if not node.meta.get("saved_tensor_with_no_vc_check", False):
                    raise AssertionError(
                        f"i={i}, no_vc_check_start_idx={no_vc_check_start_idx}, len(saved_values)={len(saved_values)}"
                    )

        # Now, we re-generate the fwd/bwd graphs.
        # NB: This might increase compilation time, but I doubt it matters
        # Convention for saved acts is (tensors_with_vc_check, tensors_no_vc_check, opaque_objects, symints, opaque_nodes)
        fwd_graph = _extract_graph_with_inputs_outputs(
            joint_module.graph,
            primal_inputs + fwd_seed_offset_inputs,
            fwd_outputs
            + saved_values
            + saved_opaque_objects
            + saved_opaque_nodes
            + saved_sym_nodes,
            fwd_outputs_descs
            + [
                SavedForBackwardsNoVcCheckAOTOutput(i)
                if i >= no_vc_check_start_idx and i < len(saved_values)
                else SavedForBackwardsAOTOutput(i)
                for i in range(
                    len(saved_values)
                    + len(saved_opaque_objects)
                    + len(saved_opaque_nodes)
                    + len(saved_sym_nodes)
                )
            ],
            "forward",
            ignore_must_be_in_fw_bw=ignore_must_be_in_fw_bw,
        )
        bwd_graph = _extract_graph_with_inputs_outputs(
            joint_module.graph,
            saved_sym_nodes
            + saved_values
            + saved_opaque_objects
            + saved_opaque_nodes
            + tangent_inputs
            + bwd_seed_offset_inputs
            + backward_state_inputs,
            bwd_outputs,
            bwd_outputs_descs,
            "backward",
            ignore_must_be_in_fw_bw=ignore_must_be_in_fw_bw,
        )
    else:
        # Raw fwd/bwd split for direct execution without autograd
        fwd_graph = _extract_graph_with_inputs_outputs(
            joint_module.graph,
            primal_inputs + fwd_seed_offset_inputs,
            fwd_outputs + saved_values + saved_sym_nodes,
            fwd_outputs_descs
            + [
                SavedForBackwardsAOTOutput(i)
                for i in range(len(saved_values) + len(saved_sym_nodes))
            ],
            "forward",
            ignore_must_be_in_fw_bw=ignore_must_be_in_fw_bw,
        )
        bwd_graph = _extract_graph_with_inputs_outputs(
            joint_module.graph,
            saved_values
            + saved_sym_nodes
            + bwd_seed_offset_inputs
            + backward_state_inputs,
            bwd_outputs,
            bwd_outputs_descs,
            "backward",
            ignore_must_be_in_fw_bw=ignore_must_be_in_fw_bw,
        )

    fwd_module = fx._lazy_graph_module._make_graph_module(joint_module, fwd_graph)
    bwd_module = fx._lazy_graph_module._make_graph_module(joint_module, bwd_graph)
    if (
        inductor_config.post_grad_fusion_options.get(
            "activation_quantization_aten_pass", None
        )
        is not None
    ):
        enable_activation_quantization(
            saved_values,
            fwd_module,
            bwd_module,
            static_lifetime_input_nodes,
            num_fwd_outputs,
        )
    return fwd_module, bwd_module
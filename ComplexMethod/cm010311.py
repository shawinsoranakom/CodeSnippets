def _create_stateful_graph_module(
    plain_graph_module: torch.fx.GraphModule,
    range_constraints,
    ep: ExportedProgram,
) -> _StatefulGraphModule:
    stateful_gm = _StatefulGraphModule._create(
        plain_graph_module,
        plain_graph_module.graph,
        range_constraints=range_constraints,
    )

    module_types = _get_graph_inputs_of_type_nn_module(ep.example_inputs)
    stateful_gm.register_forward_pre_hook(
        lambda *args, **kwargs: _enter_enable_graph_inputs_of_type_nn_module(
            module_types
        )
    )
    stateful_gm.register_forward_pre_hook(
        _check_input_constraints_pre_hook, with_kwargs=True
    )

    stateful_gm.register_forward_hook(
        lambda *args, **kwargs: _exit_enable_graph_inputs_of_type_nn_module(
            module_types
        ),
        always_call=True,
    )

    # When we have a constant that has requires_grad=True, we need to detach it
    # when we unlift as the tensors that require gradients should be registered
    # via parameters. But this is problematic when we have aliasing two constants
    # because when we call detach, they will become different tensors. This dict
    # keeps track of this logic.
    original_tensor_to_detached_tensor = {}

    # Fix up lifted tensor constants.
    # fx.GraphModule() constructor silently turns a constant attribute of plain_graph_module
    # into a buffer in stateful_gm and creates an inconsistency with graph_signature.
    # We fix this by de-registering these buffers in lifted_tensor_constants
    # and call _assign_attr(attr_kind=CONSTANT) to register them as constants.
    for constant_fqn in ep.graph_signature.lifted_tensor_constants:
        # Sometimes, the constant can require gradient, this is probably a bug in user code,
        # e.g. `self.const = torch.randn(2, 2, requires_grad=True)`.
        # We call detach on the constant_val since they're tensor constants and we don't need to
        # compute their gradients anyway.
        # Users should properly register it as parameter if they want it to require gradient.
        buffer = stateful_gm.get_buffer(constant_fqn)
        if buffer.requires_grad:
            warnings.warn(
                f"A model attribute `{constant_fqn}` requires gradient. "
                f"but it's not properly registered as a parameter. "
                f"torch.export will detach it and treat it as a constant tensor "
                f"but please register it as parameter instead.",
                stacklevel=2,
            )
            detached_buffer = buffer.detach()
            original_tensor_to_detached_tensor[buffer] = detached_buffer
            buffer = detached_buffer
        *prefix, field = constant_fqn.rsplit(".")
        submod = torch.fx.graph_module._get_attr_via_attr_list(stateful_gm, prefix)
        delattr(submod, field)
        _assign_attr(buffer, stateful_gm, constant_fqn, attr_kind=_AttrKind.CONSTANT)

    # Constants are not preserved well when we create a new GraphModule unlike param/buffers
    for const_name, value in ep.constants.items():
        if not torch.fx.graph_module._has_attr(stateful_gm, const_name):
            if isinstance(value, torch.Tensor):
                if value.requires_grad:
                    warnings.warn(
                        f"A model attribute `{const_name}` requires gradient "
                        f"but it's not properly registered as a parameter. "
                        f"torch.export will detach it and treat it as a constant tensor "
                        f"but please register it as parameter instead.",
                        stacklevel=2,
                    )
                    if value in original_tensor_to_detached_tensor:
                        value = original_tensor_to_detached_tensor[value]
                    else:
                        detached_value = value.detach()
                        original_tensor_to_detached_tensor[value] = detached_value
                        value = detached_value
            _assign_attr(
                value,
                stateful_gm,
                const_name,
                attr_kind=_AttrKind.CONSTANT,
            )

    # Fix up non-persistent buffers. torch.fx does not distinguish between
    # persistent and non-persistent buffers, so we must restore that distinction
    # here.
    for buffer in ep.graph_signature.non_persistent_buffers:
        _assign_attr(
            plain_graph_module.get_buffer(buffer),
            stateful_gm,
            buffer,
            attr_kind=_AttrKind.BUFFER,
            persistent=False,
        )

    return stateful_gm
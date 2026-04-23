def _export_for_training(
    mod: torch.nn.Module,
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None = None,
    *,
    strict: bool = True,
    preserve_module_call_signature: tuple[str, ...] = (),
    prefer_deferred_runtime_asserts_over_guards: bool = False,
) -> ExportedProgram:
    global _EXPORT_MODULE_HIERARCHY
    _EXPORT_MODULE_HIERARCHY = _get_module_hierarchy(mod)

    (
        args,
        kwargs,
        orig_in_spec,
        dynamic_shapes,
        verify_additional_inputs,
    ) = _process_export_inputs(mod, args, kwargs, dynamic_shapes)

    original_state_dict = _get_original_state_dict(mod)

    has_ambient_mode = False
    if not strict:
        flat_args, _ = pytree.tree_flatten((args, kwargs))
        has_ambient_mode = torch._guards.detect_fake_mode(flat_args) is not None

    # Call the appropriate export function based on the strictness of tracing.
    export_func = _strict_export if strict else _non_strict_export

    if not strict and torch._export.config.detect_non_strict_fake_tensor_leaks:
        from torch._subclasses.fake_tensor import fake_tensor_tls

        fake_tensor_tls.non_strict_export_fake_tensor_tracker.clear()

    export_artifact = export_func(
        mod=mod,
        args=args,
        kwargs=kwargs,
        dynamic_shapes=dynamic_shapes,
        preserve_module_call_signature=preserve_module_call_signature,
        orig_in_spec=orig_in_spec,
        prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
        _to_aten_func=_export_to_aten_ir_make_fx,
    )

    # If we are tracing with fake inputs, it is expected to
    # see fake tensor constants.
    if not strict and not has_ambient_mode:
        for const, val in export_artifact.aten.constants.items():
            if isinstance(
                val, torch._subclasses.fake_tensor.FakeTensor
            ) and _is_bogus_const_name(const):
                error_msg = (
                    f"We found a fake tensor in the exported program constant's list. "
                    f"This typically means our tracing system encountered an op that "
                    f"we can't trace through. For the potential source, you can refer to "
                    f"following model attribute: {const}. "
                    f"Please file an issue on github. "
                )
                if torch._export.config.error_on_lifted_constant_tensors:
                    raise RuntimeError(error_msg)
                else:
                    warnings.warn(error_msg, stacklevel=2)

    export_graph_signature = export_artifact.aten.sig

    forward_arg_names = _get_forward_arg_names(mod, args, kwargs)
    inline_constraints = _get_inline_constraints(export_artifact.fake_mode)
    # The unbacked symint symbols are updated in aot_export
    # so we serialize them here instead of inside dynamo.
    # Note: _get_range_constraints depends on "inline_constraints" to be set.
    export_artifact.aten.gm.meta["inline_constraints"] = inline_constraints
    range_constraints = _get_range_constraints(
        mod,
        export_artifact,
        args,
        kwargs,
        dynamic_shapes,
    )
    # The returned the gm is in-place modified
    gm, module_call_graph = _get_module_call_graph(
        export_artifact,
        preserve_module_call_signature,
        strict,
        forward_arg_names,
    )

    _verify_nn_module_stack(gm)
    _verify_stack_trace(gm)
    _verify_placeholder_names(gm, export_graph_signature)

    _update_gm_meta_if_possible(gm, mod)

    from torch._export.verifier import TrainingIRVerifier

    exported_program = ExportedProgram(
        root=gm,
        graph=gm.graph,
        graph_signature=export_graph_signature,
        state_dict=original_state_dict,
        range_constraints=range_constraints,
        module_call_graph=module_call_graph,
        example_inputs=(args, kwargs),
        constants=export_artifact.aten.constants,
        verifiers=[TrainingIRVerifier],
    )

    verify_additional_inputs(exported_program)

    if not strict and torch._export.config.detect_non_strict_fake_tensor_leaks:
        # See NOTE [export non-strict fake tensor leak detection]
        from torch._subclasses.fake_tensor import fake_tensor_tls
        from torch.fx.experimental.proxy_tensor import (
            _FAKE_TENSOR_ID_TO_PROXY_MAP_FOR_EXPORT,
        )

        active_fakes = fake_tensor_tls.non_strict_export_fake_tensor_tracker
        legit_leak: weakref.WeakSet = find_legit_leaks_from_referrers(active_fakes)
        leak_sources: list[str] = []
        if len(legit_leak) > 0:
            for fake_val in legit_leak:
                if id(fake_val) in _FAKE_TENSOR_ID_TO_PROXY_MAP_FOR_EXPORT:
                    node = _FAKE_TENSOR_ID_TO_PROXY_MAP_FOR_EXPORT[id(fake_val)]
                    stack_trace = node.meta.get("stack_trace")
                    node_name = node.name

                    # If no stack trace on this node (e.g., placeholder), look at users
                    if stack_trace is None:
                        for user in node.users:
                            user_stack = user.meta.get("stack_trace")
                            if user_stack is not None:
                                stack_trace = f"Used by '{user.name}':\n{user_stack}"
                                break

                    stack_trace = (
                        "<no stack trace available>"
                        if stack_trace is None
                        else stack_trace
                    )

                    # Get shape and dtype info
                    shape_info = f"shape={fake_val.shape}, dtype={fake_val.dtype}"
                    leak_info = f"FakeTensor({shape_info}) from node '{node_name}':\n{stack_trace}"
                    leak_sources.append(leak_info)
                else:
                    # Fallback: no proxy mapping found, show basic info
                    shape_info = f"shape={fake_val.shape}, dtype={fake_val.dtype}"
                    leak_info = f"FakeTensor({shape_info}): <no proxy mapping found>"
                    leak_sources.append(leak_info)

            # Format the warning message more nicely
            leak_details = "\n  ".join(leak_sources)
            warnings.warn(
                f"Detected {len(legit_leak)} fake tensors that are still alive after export.\n"
                f"This is likely result of torch.export.export not being able to track side effects "
                f"that is happening outside of model scope.\n\n"
                f"Leaked tensors:\n  {leak_details}\n\n"
                f"Alternatively, please file a bug report to PyTorch team for further debugging help.",
                stacklevel=2,
            )

            del legit_leak

    return exported_program
def _export_to_torch_ir(
    f: Callable,
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None = None,
    *,
    preserve_module_call_signature: tuple[str, ...] = (),
    disable_constraint_solver: bool = False,
    prefer_deferred_runtime_asserts_over_guards: bool = False,
    restore_fqn: bool = True,
    _log_export_usage: bool = True,
    same_signature: bool = True,
) -> torch.fx.GraphModule:
    """
    Traces either an nn.Module's forward function or just a callable with PyTorch
    operations inside and produce a torch.fx.GraphModule in torch IR.
    """

    if _log_export_usage:
        log_export_usage(event="export.private_api", flags={"_export_to_torch_ir"})

    if not isinstance(args, tuple):
        raise UserError(
            UserErrorType.INVALID_INPUT,
            f"Expecting `args` to be a tuple of example positional inputs, got {type(args)}",
        )

    kwargs = kwargs or {}

    # Map ints to a wrapper structure to help us mark it as dynamic, if it is
    # dynamic. We will unwrap ints in fakify later.
    args, kwargs = pytree.tree_map_only(int, _IntWrapper, (args, kwargs))

    combined_args = _combine_args(f, args, kwargs)
    _check_dynamic_shapes(combined_args, dynamic_shapes)
    constraints = _process_dynamic_shapes(combined_args, dynamic_shapes)

    # Unwrap static ints -- in the case where we have an empty graph
    # containing just integer computation, dynamo will run its generated
    # bytecode with these args/kwargs, which will error because we cannot
    # directly apply int operations on IntWrapper. So we will just unwrap
    # them here.
    args, kwargs = pytree.tree_map_only(
        _IntWrapper,
        lambda a: a.val
        if a.dynamism is None or a.dynamism.type == _DimHintType.STATIC
        else a,
        (args, kwargs),
    )

    dynamo_cfg = dataclasses.replace(
        DEFAULT_EXPORT_DYNAMO_CONFIG,
        prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
    )

    def use_legacy_dynamo_graph_capture() -> bool:
        return bool(
            constraints  # dynamic shape
            or dynamic_shapes  # dynamic shape
            or isinstance(f, torch.fx.GraphModule)  # retracing
            or preserve_module_call_signature  # unflatten
            or torch._functorch.config.fake_tensor_propagate_real_tensors  # draft
            or torch._export.config.use_legacy_dynamo_graph_capture
        )

    with torch._dynamo.config.patch(dataclasses.asdict(dynamo_cfg)):
        try:
            module_call_specs: dict[str, dict[str, pytree.TreeSpec]] = (
                _ExportModuleSpecTrackerDict()
            )
            ctx = nullcontext()
            if not isinstance(f, torch.fx.GraphModule):
                ctx = _wrap_submodules(  # type: ignore[assignment]
                    f, preserve_module_call_signature, module_call_specs
                )
            with ctx, _ignore_backend_decomps():
                if torch._export.config.use_new_tracer_experimental:
                    from torch._dynamo.functional_export import (
                        _dynamo_graph_capture_for_export,
                        dynamo_graph_capture_for_export,
                    )

                    if use_legacy_dynamo_graph_capture():
                        dynamo_graph_capture = _dynamo_graph_capture_for_export(
                            f, constraints=constraints, dynamic_shapes=dynamic_shapes
                        )
                    else:
                        dynamo_graph_capture = torch._dynamo.config.patch(
                            replay_side_effects=False
                        )(dynamo_graph_capture_for_export(f))
                    # We can't serialize entire fake mode yet, so this is to make sure
                    # things like copy.deepcopy(ep.graph_module) not crash.
                    # see test_export.py::test_custom_tag_metadata_re_export
                    # Once we delete the old strict export, we can use
                    gm_torch_level = dynamo_graph_capture(*args, **kwargs)
                    # We can't serialize entire fake mode yet, so this is to make sure
                    # things like copy.deepcopy(ep.graph_module) not crash.
                    # see test_export.py::test_custom_tag_metadata_re_export
                    # Once we delete the old strict export, we can use this fake mode in the
                    # subsequent logic when lowering to aten IR.
                    del gm_torch_level.meta["fake_mode"]

                else:
                    gm_torch_level, _ = torch._dynamo.export(
                        f,
                        dynamic_shapes=dynamic_shapes,  # type: ignore[arg-type]
                        constraints=constraints,  # type: ignore[arg-type]
                        assume_static_by_default=True,
                        tracing_mode="symbolic",
                        disable_constraint_solver=disable_constraint_solver,
                        prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
                        _log_export_usage=_log_export_usage,
                        same_signature=same_signature,
                    )(
                        *args,
                        **kwargs,
                    )
                    gm_torch_level.meta["module_call_specs"] = module_call_specs
        except (ConstraintViolationError, ValueRangeError) as e:
            raise UserError(UserErrorType.CONSTRAINT_VIOLATION, str(e))  # noqa: B904
        except GuardOnDataDependentSymNode as e:
            raise UserError(  # noqa: B904
                UserErrorType.ANTI_PATTERN,
                f"Consider annotating your code using torch._check*(). {str(e)}",
                case_name="constrain_as_size_example",
            )

    if isinstance(f, torch.nn.Module) and restore_fqn:
        _restore_state_dict(f, gm_torch_level)

    return gm_torch_level
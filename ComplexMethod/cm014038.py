def aot_compile_fullgraph(
    model: Any,
    example_inputs: tuple[tuple[Any, ...], dict[str, Any]],
    hooks: Hooks,
    backend: Callable[[torch.fx.GraphModule, list[torch.Tensor]], SerializableCallable],
    dynamic: bool | None = None,
) -> AOTCompiledFunction:
    from torch._dynamo.guards import CheckFunctionManager
    from torch._dynamo.package import SourceInfo
    from torch._dynamo.utils import dynamo_timed, get_metrics_context
    from torch._dynamo.variables.torch_function import (
        torch_function_mode_stack_state_mgr,
    )
    from torch._guards import TracingContext

    args, kwargs = example_inputs

    dynamic_ctx = nullcontext()
    if dynamic is not None:
        from torch._dynamo.eval_frame import set_enable_dynamic

        dynamic_ctx = set_enable_dynamic(dynamic)

    with (
        get_metrics_context(),
        dynamo_timed("fullgraph_capture"),
        torch._functorch.config.patch(strict_autograd_cache=True),
        dynamic_ctx,
        torch_function_mode_stack_state_mgr,
    ):
        capture_output = convert_frame.fullgraph_capture(model, args, kwargs)
        graph_capture_output = capture_output.graph_capture_output
        assert graph_capture_output.output_graph is not None

        if not hooks.guard_filter_fn:
            from torch._dynamo.types import GuardFilterEntry

            def new_guard_filter_fn(
                guard_entries: Sequence[GuardFilterEntry],
            ) -> Sequence[bool]:
                return [
                    (
                        not (
                            g.is_global
                            or g.guard_type
                            in CheckFunctionManager.UNSUPPORTED_SERIALIZATION_GUARD_TYPES
                        )
                    )
                    for g in guard_entries
                ]

            hooks.guard_filter_fn = new_guard_filter_fn

        fn, _ = convert_frame.get_traced_fn(model)

        backend_input = capture_output.backend_input
        assert backend_input is not None
        backend_input.graph_module._backend_id = backend_input.backend_id  # type: ignore[assignment]
        device_type = _graph_device_type(backend_input.graph_module.graph)
        assert (
            backend_input.fake_mode.shape_env
            is graph_capture_output.output_graph.shape_env
        )
        tracing_context = TracingContext(backend_input.fake_mode)
        tracing_context.tensor_to_context = backend_input.tensor_to_context
        with (
            torch._guards.tracing(tracing_context),
            torch._functorch.config.patch(
                {
                    "strict_autograd_cache": True,
                    "bypass_autograd_cache_key": True,
                    "bundled_autograd_cache": True,
                    "force_non_lazy_backward_lowering": True,
                    "force_autograd_cache": True,
                }
            ),
        ):
            compiled_fn = backend(
                backend_input.graph_module, backend_input.example_inputs
            )
            # If Inductor backend or AOTAutograd-based backend is used,
            # wrap the compiled_fn for serialization.
            # TODO: this should be replaced once we make the backend return the SerializableCallable directly.
            if (
                isinstance(backend, torch._TorchCompileInductorWrapper)
                or (
                    hasattr(backend, "compiler_fn")
                    and isinstance(
                        backend.compiler_fn, torch._dynamo.backends.common.AotAutograd
                    )
                )
                or (
                    hasattr(compiled_fn, "serialize")
                    and compiled_fn.serialize is not None
                )
            ):
                compiled_fn = BundledAOTAutogradSerializableCallable(compiled_fn)

        if not isinstance(compiled_fn, SerializableCallable):
            if hasattr(backend, "compiler_fn"):
                compiler_fn = backend.compiler_fn
            else:
                compiler_fn = backend
            raise RuntimeError(
                f"Compiled function type {type(compiled_fn)} (produced "
                + f"from backend {compiler_fn}) does not implement SerializableCallable."
            )

        # Temporarily restore the mode stack so guard expressions that
        # reference modes can evaluate, matching the compile_inner path.
        build_guards_ctx = ExitStack()
        if torch_function_mode_stack_state_mgr.stack:
            build_guards_ctx.enter_context(
                torch_function_mode_stack_state_mgr.temp_restore_stack()
            )
        with build_guards_ctx:
            check_fn = graph_capture_output.build_guards(
                fn.__code__, hooks=hooks, save=True, strict_error=True
            )

        assert check_fn.guards_state is not None

        source_info = SourceInfo(inlined_sources=set())
        for traced_code in graph_capture_output.traced_code:
            source_info.add_code(traced_code)

        artifacts = CompileArtifacts(
            signature=convert_frame._get_signature(fn),
            guard_manager=check_fn.guard_manager,
            guards_state=check_fn.guards_state,
            backend_id=backend_input.backend_id,
            compiled_fn=compiled_fn,
            original_code=fn.__code__,
            runtime_env=graph_capture_output.get_runtime_env(),
            source_info=source_info,
            device_type=device_type,
            backend_name=getattr(backend, "compiler_name", "unknown"),
        )
        aot_compiled_fn = AOTCompiledFunction(
            _artifacts=artifacts, _extra_globals=fn.__globals__
        )

    return aot_compiled_fn
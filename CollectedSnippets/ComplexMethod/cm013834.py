def record_compilation_metrics(
    start_time_ns: int,
    end_time_ns: int,
    metrics: dict[str, Any],
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
) -> None:
    if torch._inductor.utils.should_use_remote_fx_graph_cache():
        try:
            from torch._inductor.fb.remote_cache import REMOTE_CACHE_VERSION

            remote_cache_version = REMOTE_CACHE_VERSION
            inductor_fx_remote_cache_backend_type = "_ManifoldCache"
        except ModuleNotFoundError:
            remote_cache_version = None
            inductor_fx_remote_cache_backend_type = None
    else:
        inductor_fx_remote_cache_backend_type = None
        remote_cache_version = None

    # Populate the compile_id from the metrics context if it's set. Otherwise,
    # look for it in the current compile context.
    compile_id = metrics.get("compile_id")
    if not compile_id:
        compile_id = torch._guards.CompileContext.current_compile_id()

    common_metrics = {
        "compile_id": compile_id,
        "start_time_us": start_time_ns // 1000,
        "end_time_us": end_time_ns // 1000,
        "fail_type": exc_type.__qualname__ if exc_type else None,
        "fail_reason": str(exc_value) if exc_value else None,
        "structured_logging_overhead_us": to_int_us(
            torch._logging.get_structured_logging_overhead()
        ),
        "dynamo_config": _get_dynamo_config_for_logging(),
        "config_suppress_errors": config.suppress_errors,
        "config_inline_inbuilt_nn_modules": True,
        "inductor_config": _scrubbed_inductor_config_for_logging(),
        "compiler_config": _compiler_config_for_logging(),
        "cuda_version": torch.version.cuda,
        "triton_version": triton.__version__ if has_triton() else "",
        "remote_cache_version": remote_cache_version,
        "inductor_fx_remote_cache_backend_type": inductor_fx_remote_cache_backend_type,
        "python_version": sys.version,
        "pytorch_version": torch.__version__,
    }

    compilation_metrics = CompilationMetrics.create({**common_metrics, **metrics})
    _compilation_metrics.append(compilation_metrics)

    name = "compilation_metrics"
    if compilation_metrics.is_forward is False:
        name = "bwd_" + name
    if compilation_metrics.is_runtime is True:
        name = name + "_runtime"

    torch._logging.trace_structured(
        name,
        lambda: {
            k: list(v) if isinstance(v, set) else v
            for k, v in dataclasses.asdict(compilation_metrics).items()
        },
        # NB: Because compilation metrics *includes* the logging overhead time,
        # we can't both *measure* the logging overhead of compilation metrics
        # without making it inconsistent with compilation metrics itself, so
        # we ignore the (hopefully small) time spent logging compilation metrics
        record_logging_overhead=False,
        # These may be runtime logs, e.g., runtime autotunning, so we provide
        # the CompileId from the compilation metrics in case it's not available
        # in the current trace.
        compile_id=compile_id,
    )

    # If there's a chromium event in flight, add the CompilationMetrics to it.
    add_compilation_metrics_to_chromium(compilation_metrics)

    # Finally log the compilation metrics.
    if config.log_compilation_metrics:
        log_compilation_event(compilation_metrics)
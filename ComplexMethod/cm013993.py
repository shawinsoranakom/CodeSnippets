def _optimize(
    rebuild_ctx: Callable[[], OptimizeContext | _NullDecorator],
    backend: str | Callable[..., Any] = "inductor",
    *,
    nopython: bool = False,
    error_on_graph_break: bool | None = None,
    guard_export_fn: Callable[[_guards.GuardsSet], None] | None = None,
    guard_fail_fn: Callable[[GuardFail], None] | None = None,
    guard_filter_fn: Callable[[Sequence[GuardFilterEntry]], Sequence[bool]]
    | None = None,
    disable: bool = False,
    dynamic: bool | None = None,
    package: CompilePackage | None = None,
    recompile_limit: int | None = None,
) -> OptimizeContext | _NullDecorator:
    """
    The main entrypoint of TorchDynamo.  Do graph capture and call
    backend() to optimize extracted graphs.

    Args:
        backend: One of the two things:
            - Either, a function/callable taking a torch.fx.GraphModule and
            example_inputs and returning a python callable that runs the
            graph faster.
            One can also provide additional context for the backend, like
            torch.jit.fuser("fuser2"), by setting the backend_ctx_ctor attribute.
            See AOTAutogradMemoryEfficientFusionWithContext for the usage.
            - Or, a string backend name in `torch._dynamo.list_backends()`
        nopython: If True, graph breaks will be errors and there will
            be a single whole-program graph.
        error_on_graph_break: If not None, the current `error_on_graph_break` setting is set to the given value.
            See `torch._dynamo.error_on_graph_break()` for more details on what `error_on_graph_break` means.

            Unlike `nopython=True` (i.e. `fullgraph=True`), there is no guarantee of a single whole-program graph.
            If `nopython` is True, `error_on_graph_break` does nothing.
        disable: If True, turn this decorator into a no-op
        dynamic: If True, upfront compile as dynamic a kernel as possible.  If False,
            disable all dynamic shapes support (always specialize).  If None, automatically
            detect when sizes vary and generate dynamic kernels upon recompile.

    Example Usage::

        @torch._dynamo.optimize()
        def toy_example(a, b): ...
    """
    check_if_dynamo_supported()
    check_for_incompatible_configs()
    # Note: The hooks object could be global instead of passed around, *however* that would make
    # for a confusing API usage and plumbing story wherein we nest multiple .optimize calls.
    # There is some prior art around this, w/r/t nesting backend calls are enforced to be the same
    # compiler, however, this feels onerous for callback and hooks, and it feels better to give our users an
    # easier to understand UX at the cost of a little more plumbing on our end.
    hooks = Hooks(
        guard_export_fn=guard_export_fn,
        guard_fail_fn=guard_fail_fn,
        guard_filter_fn=guard_filter_fn,
    )
    torch._C._log_api_usage_once("torch._dynamo.optimize")
    if (
        disable
        or os.environ.get("TORCHDYNAMO_DISABLE", "") == "1"
        or (not justknobs_check("pytorch/compiler:enable_dynamo"))
    ):
        return _NullDecorator()

    if nopython and not config.debug_force_graph_break_on_leaf_return:
        return optimize_assert(
            backend,
            dynamic=dynamic,
            hooks=hooks,
            rebuild_ctx=rebuild_ctx,
            package=package,
            recompile_limit=recompile_limit,
        )

    backend = get_compiler_fn(backend)

    # Find if backend has any extra context manager
    backend_ctx_ctor = getattr(backend, "backend_ctx_ctor", null_context)

    # The backend function is stashed in the callable returned by
    # _optimize_catch_errors in the field _torchdynamo_orig_backend. This can
    # be used by eval_frame.c to insert a guard on the backend.

    # With CachingPrecompile, instantiate an uninitialized CompilePackage
    # which gets initialized by _optimize_catch_errors.__call__ once we have a function
    if config.caching_precompile and package is None:
        from .package import CompilePackage

        package = CompilePackage(fn=None, dynamo=None, ignore_inlined_sources=False)

    return _optimize_catch_errors(
        convert_frame.convert_frame(
            backend,
            hooks,
            package=package,
            recompile_limit=recompile_limit,
        ),
        hooks,
        backend_ctx_ctor,
        fullgraph=False,
        error_on_graph_break=error_on_graph_break
        and not config.debug_force_graph_break_on_leaf_return,
        dynamic=dynamic,
        compiler_config=(
            backend.get_compiler_config()
            if hasattr(backend, "get_compiler_config")
            else None
        ),
        rebuild_ctx=rebuild_ctx,
        package=package,
    )
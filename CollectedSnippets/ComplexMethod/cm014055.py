def _enable(
    compiler_fn: Callable[..., Any],
    dynamic: bool = True,
    ignore_active_disable_ctx: bool = True,
) -> Generator[None, None, None]:
    # The entrypoint to enable CA.
    # It is recommended to enable via `torch._dynamo.config.compiled_autograd = True` rather
    # than using this context manager directly. If you are torch.compiling the corresponding
    # forward pass, make sure they are wrapped under this context as well.
    #
    # Example:
    #   def train(model, inputs, target):
    #     compiled_model = torch.compile(model)
    #     pred = compiled_model(data)
    #     loss = compute_loss(pred, target)
    #     loss.backward()
    #
    #   with _enable(compiler_fn):
    #      train(model, inputs, target)
    #
    # Inputs:
    # - compiler_fn: The wrapper that will consume the compiled autograd graph, e.g. `torch.compile`
    # - dynamic: Whether compiled autograd will treat tensors in the autograd graph (params, activations) as dynamic.
    #   This doesn't affect the dynamic configuration of the compilation wrapper.

    if not ignore_active_disable_ctx and active_disable_ctx:
        yield
    else:
        if dynamic:
            assert type(dynamic) is bool

        from torch._dynamo import eval_frame

        if eval_frame._stance.stance == "force_eager":
            # If user explicitly sets Dynamo stance to "force_eager", we want Compiled Autograd
            # to fall back to eager as well.
            global compiled_autograd_enabled_force_eager
            compiled_autograd_enabled_force_eager = True
            try:
                yield
            finally:
                compiled_autograd_enabled_force_eager = False
        else:
            # we need to import this, because user might not have imported it if they directly use this context manager
            # we need to lazily import it, because of circular dependencies
            if torch.cuda.is_available():
                from torch._inductor import cudagraph_trees  # noqa: F401

            (
                prior_compiler,
                prior_dynamic,
            ) = torch._C._dynamo.compiled_autograd.set_autograd_compiler(
                functools.partial(AutogradCompilerInstance, compiler_fn), dynamic
            )
            if snapshot_verbose_logging_enabled():
                torch._C._dynamo.compiled_autograd.set_verbose_logger(verbose_log)  # type:ignore[arg-type]
            global compiled_autograd_enabled
            compiled_autograd_enabled = True
            global depth
            prior_depth = depth
            depth += 1
            try:
                with torch.autograd.set_multithreading_enabled(False):
                    yield
            finally:
                if not prior_compiler:
                    compiled_autograd_enabled = False
                torch._C._dynamo.compiled_autograd.set_autograd_compiler(
                    prior_compiler, prior_dynamic
                )
                depth -= 1
                assert depth == prior_depth, (
                    "Nested Compiled Autograd Contexts must return before their parent context"
                )
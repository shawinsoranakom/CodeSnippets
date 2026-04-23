def _functional_call(
    module: "torch.nn.Module",
    parameters_and_buffers: dict[str, Tensor],
    args: Any | tuple | None = None,
    kwargs: dict[str, Any] | None = None,
    *,
    tie_weights: bool = True,
    strict: bool = False,
):
    # TODO allow kwargs such as unsafe and others for parametrization
    if (
        torch.jit.is_tracing()
        or torch.jit.is_scripting()
        or isinstance(
            module,
            (
                torch.jit.RecursiveScriptModule,
                torch.jit.ScriptModule,
                torch.jit.ScriptFunction,
            ),
        )
    ):
        raise RuntimeError("The stateless API can't be used with Jitted modules")
    if isinstance(module, torch.nn.DataParallel):
        raise RuntimeError(
            "The stateless API can't be used with nn.DataParallel module"
        )
    if kwargs is None:
        kwargs = {}
    if args is None:
        args = ()
    elif not isinstance(args, tuple):
        args = (args,)
    with _reparametrize_module(
        module, parameters_and_buffers, tie_weights=tie_weights, strict=strict
    ):
        return module(*args, **kwargs)
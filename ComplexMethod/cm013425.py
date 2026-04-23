def _get_qualified_name(func: Callable[..., Any]) -> str:
    # things like getattr just appear in builtins
    if getattr(builtins, func.__name__, None) is func:
        return func.__name__
    # torch.Tensor.{fn}
    if (
        isinstance(func, (types.MethodDescriptorType, types.WrapperDescriptorType))
        and func is getattr(torch.Tensor, func.__name__, None)
    ) or (
        func.__module__ == torch._tensor.__name__
        and func.__qualname__ == f"Tensor.{func.__name__}"
    ):
        return f"torch.Tensor.{func.__name__}"
    name = func.__name__

    if name == "<lambda>":
        # For lambdas, try to get their defining name in the module
        try:
            name = inspect.getsource(func).split("=")[0].strip()
        except Exception as e:
            raise RuntimeError("Unable to represent lambda") from e
    module = _find_module_of_method(func)
    module = module.replace(
        "torch._ops", "torch.ops"
    )  # WAR for bug in how torch.ops assigns module
    # Fixup segment_reduce mismatch
    if module == "torch" and name == "segment_reduce":
        name = "_" + name
    if module == "torch.nn.functional" and name in ("_ScalingType", "_SwizzleType"):
        name = name.removeprefix("_")
    return f"{module}.{name}"
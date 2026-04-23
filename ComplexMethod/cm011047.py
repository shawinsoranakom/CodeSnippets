def _recursive_wrap(
    module: nn.Module,
    auto_wrap_policy: Callable,
    wrapper_cls: Callable,
    ignored_modules: set[nn.Module],
    ignored_params: set[nn.Parameter],
    only_wrap_children: bool = False,
    **kwargs: Any,
) -> tuple[nn.Module, int]:
    """
    Wraps submodules of ``module`` for which ``auto_wrap_policy`` returns
    ``True`` with ``wrapper_cls``.

    Args:
        module (nn.Module): Module to recursively wrap.
        auto_wrap_policy (Callable): A callable representing a policy that
            determines which modules to recursively wrap with ``wrapper_cls``.
        ignored_modules (set[torch.nn.Module]): Modules to ignore when
            wrapping.
        ignored_params (set[torch.nn.Parameter]): Parameters to ignore when
            wrapping; these should be the parameters contained in the modules
            in ``ignored_modules``.
    Returns:
        (nn.Module, int):
            ``module`` after wrapping and the numel recursively wrapped.
    """
    if auto_wrap_policy is None:
        raise AssertionError("Must specify auto_wrap_policy.")
    if wrapper_cls is None:
        raise AssertionError("Must specify wrapper_cls")
    # Make sure no child is already wrapped.
    for _, child in module.named_modules():
        if child in ignored_modules:
            continue
        try:
            if isinstance(child, cast(type, wrapper_cls)):
                raise AssertionError(
                    f"Child module {child} is already wrapped by {wrapper_cls}"
                )
        except TypeError:
            # wrapper_cls is a function as opposed to a class type, just bypass above check.
            pass

    # We count all params, assuming none of them are already wrapped.
    nonwrapped_numel = sum(
        p.numel() for p in module.parameters() if p not in ignored_params
    )

    if auto_wrap_policy is None:
        raise AssertionError("Expected auto_wrap_policy to be set")
    if auto_wrap_policy(module=module, recurse=True, nonwrapped_numel=nonwrapped_numel):
        total_wrapped_numel = 0
        # Iterate through the children, recursively wrap if necessary
        for name, child in module.named_children():
            if child in ignored_modules:
                continue
            wrapped_child, num_wrapped_params = _recursive_wrap(
                module=child,
                auto_wrap_policy=auto_wrap_policy,
                wrapper_cls=wrapper_cls,
                ignored_modules=ignored_modules,
                ignored_params=ignored_params,
                **kwargs,
            )
            setattr(module, name, wrapped_child)
            # Keep track of how many parameters have been wrapped
            total_wrapped_numel += num_wrapped_params
        # decide if we need to wrap the current module,
        # since the left over parameters exceed the number of params to wrap
        remainder = nonwrapped_numel - total_wrapped_numel
        if not only_wrap_children and auto_wrap_policy(
            module=module, recurse=False, nonwrapped_numel=remainder
        ):
            # Leaf node or final wrapping of the remainder both happen here.
            return _wrap(module, wrapper_cls, **kwargs), nonwrapped_numel
        else:
            return module, total_wrapped_numel
    return module, 0
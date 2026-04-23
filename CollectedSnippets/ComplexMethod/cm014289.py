def _disable_current_modes():
    from torch._ops import (
        _len_torch_dispatch_stack_pre_dispatch,
        _pop_mode_from_pre_dispatch,
    )
    from torch._subclasses.functional_tensor import FunctionalTensorMode
    from torch._subclasses.schema_check_mode import SchemaCheckMode
    from torch.fx.experimental.proxy_tensor import ProxyTorchDispatchMode

    mode_len_pre_dispatch = _len_torch_dispatch_stack_pre_dispatch()
    old_pre_dispatch_modes = [
        _pop_mode_from_pre_dispatch() for _ in range(mode_len_pre_dispatch)
    ]

    has_proxy_mode_in_pre_dispatch = False
    has_functional_mode_in_pre_dispatch = False
    has_schema_check_mode_in_pre_dispatch = False

    for i in old_pre_dispatch_modes:
        if isinstance(i, ProxyTorchDispatchMode):
            has_proxy_mode_in_pre_dispatch = True
        if isinstance(i, FunctionalTensorMode):
            has_functional_mode_in_pre_dispatch = True
        if isinstance(i, SchemaCheckMode):
            has_schema_check_mode_in_pre_dispatch = True

    mode_len = _len_torch_dispatch_stack()
    old_modes = [_pop_mode() for _ in range(mode_len)]

    for old in old_modes:
        if (
            isinstance(old, FunctionalTensorMode)
            and has_functional_mode_in_pre_dispatch
        ):
            raise AssertionError(
                "Can't have FunctionalMode available both in PreDispatch and Python Key"
            )
        if isinstance(old, ProxyTorchDispatchMode) and has_proxy_mode_in_pre_dispatch:
            raise AssertionError(
                "Can't have ProxyTorchDispatchMode available both in PreDispatch and Python Key"
            )
        if isinstance(old, SchemaCheckMode) and has_schema_check_mode_in_pre_dispatch:
            raise AssertionError(
                "Can't have SchemaCheckMode available both in PreDispatch and Python Key"
            )

    # Manually disable proxy and fake modes, if any are active
    try:
        yield old_pre_dispatch_modes + old_modes
    finally:
        for mode in reversed(old_modes):
            _push_mode(mode)
        for mode in reversed(old_pre_dispatch_modes):
            _push_mode(mode)
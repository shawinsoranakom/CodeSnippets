def _set_mode_pre_dispatch(mode):
    from torch._subclasses.functional_tensor import FunctionalTensorMode
    from torch._subclasses.schema_check_mode import SchemaCheckMode
    from torch.fx.experimental.proxy_tensor import ProxyTorchDispatchMode

    if not isinstance(
        mode,
        (
            FunctionalTensorMode,
            ProxyTorchDispatchMode,
            SchemaCheckMode,
        ),
    ):
        raise AssertionError(
            f"mode must be FunctionalTensorMode, ProxyTorchDispatchMode, or SchemaCheckMode, got {type(mode)}"
        )

    previous_mode_stack_len = _len_torch_dispatch_stack_pre_dispatch()
    if isinstance(mode, SchemaCheckMode):
        current_mode = mode_stack_state_for_pre_dispatch()._schema_check_mode
        if previous_mode_stack_len > 0:
            raise AssertionError(
                "SchemaCheckMode for pre-dispatch must be used exclusively, found other modes on the stack"
            )
        mode_stack_state_for_pre_dispatch()._schema_check_mode = mode
    elif isinstance(mode, FunctionalTensorMode):
        current_mode = mode_stack_state_for_pre_dispatch().get(1)
        if current_mode is not None:
            raise AssertionError(
                f"FunctionalTensorMode slot already occupied by {current_mode}"
            )
        mode_stack_state_for_pre_dispatch().set(1, mode)
    else:
        current_mode = mode_stack_state_for_pre_dispatch().get(0)
        if current_mode is not None:
            raise AssertionError(
                f"ProxyTorchDispatchMode slot already occupied by {current_mode}"
            )
        mode_stack_state_for_pre_dispatch().set(0, mode)

    # When we are setting a mode, we need to check if there is
    # active mode left on the PreDispatch key. If there was nothing
    # active before setting this mode, it means that PreDispatch key
    # was turned off. So we need to turn it on again.
    if previous_mode_stack_len == 0:
        torch._C._dispatch_tls_set_dispatch_key_included(DispatchKey.PreDispatch, True)
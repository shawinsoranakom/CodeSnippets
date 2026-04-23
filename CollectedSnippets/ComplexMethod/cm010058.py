def register_autocast(
    op: _op_identifier,
    device_type: str,
    cast_inputs: _dtype,
    /,
    *,
    lib: Library | None = None,
):
    r"""Register an autocast dispatch rule for this custom op.

    Valid `device_type` include: "cpu" and "cuda".

    Args:
        op (str | OpOverload): The operator to register an autocast dispatch rule to.
        device_type(str):  Device type to use. 'cuda' or 'cpu'.
            The type is the same as the `type` attribute of a :class:`torch.device`.
            Thus, you may obtain the device type of a tensor using `Tensor.device.type`.
        cast_inputs (:class:`torch.dtype`): When custom op runs in an autocast-enabled region,
            casts incoming floating-point Tensors to the target dtype (non-floating-point Tensors
            are not affected), then executes custom op with autocast disabled.
        lib (Optional[Library]): If provided, the lifetime of this registration

    Examples::
        >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_CUDA)
        >>> import torch
        >>> from torch import Tensor
        >>> from torch.library import custom_op
        >>>
        >>> # Create a custom op that works on cuda
        >>> @torch.library.custom_op("mylib::my_sin", mutates_args=())
        >>> def my_sin(x: Tensor) -> Tensor:
        >>>     return torch.sin(x)
        >>>
        >>> # Register autocast dispatch rule for the cuda device
        >>> torch.library.register_autocast("mylib::my_sin", "cuda", torch.float16)
        >>>
        >>> x = torch.randn(3, dtype=torch.float32, device="cuda")
        >>> with torch.autocast("cuda", dtype=torch.float16):
        >>>     y = torch.ops.mylib.my_sin(x)
        >>> assert y.dtype == torch.float16

    """
    if not isinstance(
        op, (str, torch._ops.OpOverload, torch._library.custom_ops.CustomOpDef)
    ):
        raise ValueError(
            f"register_autocast({op}): got unexpected type for op: {type(op)}"
        )
    if device_type not in ["cpu", "cuda"]:
        raise ValueError(f"Unknown device type: {device_type}")

    if isinstance(op, torch._ops.OpOverload):
        op = op._name
    opdef = _maybe_get_opdef(op)
    if opdef is not None:
        return opdef.register_autocast(device_type, cast_inputs)

    if not isinstance(op, str):
        raise AssertionError(f"op must be str at this point, got {type(op).__name__}")
    qualname = op
    _op = torch._library.utils.lookup_op(qualname)

    namespace, opname = torch._library.utils.parse_namespace(qualname)
    if lib is None:
        lib = Library(namespace, "FRAGMENT")
        _keep_alive.append(lib)

    def _maybe_override_py_impl(op: torch._ops.OpOverload, dispatch_key):
        def inner(kernel):
            if op.has_kernel_for_dispatch_key(dispatch_key):
                op.py_kernels.pop(dispatch_key)
            return op.py_impl(dispatch_key)(kernel)

        return inner

    @_maybe_override_py_impl(_op, torch._C.DispatchKey.AutocastCPU)
    @_maybe_override_py_impl(_op, torch._C.DispatchKey.AutocastCUDA)
    def _autocast_py_impl(*args, **kwargs):
        if len(kwargs) != 0:
            raise AssertionError("Custom ops do not support kwargs yet.")
        autocast_keyset = torch._C.DispatchKeySet(
            torch._C.DispatchKey.AutocastCPU
        ) | torch._C.DispatchKeySet(torch._C.DispatchKey.AutocastCUDA)
        with torch._C._ExcludeDispatchKeyGuard(autocast_keyset):
            return _op(*_cast(args, device_type, cast_inputs))

    def kernel(_, *args, **kwargs):
        if len(kwargs) != 0:
            raise AssertionError("Custom ops do not support kwargs yet.")
        return _autocast_py_impl(*args, **kwargs)

    if device_type == "cuda":
        return lib.impl(opname, kernel, "AutocastCUDA", with_keyset=True)
    else:
        # device_type is "cpu"
        return lib.impl(opname, kernel, "AutocastCPU", with_keyset=True)
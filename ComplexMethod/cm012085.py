def custom_op_wrapper(op: str, *args: Any) -> list[c_void_p] | c_void_p | None:
    # This function will be called from generated cpp wrapper code in the JIT mode.
    # Because tensors will be passed in as AtenTensorHandle, we need to explicitly convert them.
    def convert_arg(arg: Any) -> Any:
        if str(type(arg)) == "<class 'PyCapsule'>":
            # No easy way to do isinstance check on PyCapsule
            return torch._C._aoti.alloc_tensor_by_stealing_from_void_ptr(arg)
        elif isinstance(arg, (list, tuple)):
            return type(arg)(convert_arg(a) for a in arg)
        else:
            return arg

    converted_args = [convert_arg(arg) for arg in args]

    assert op.startswith("torch.ops."), (
        op + " can not be called through custom_op_wrapper"
    )
    func = None
    for i, s in enumerate(op.split(".")):
        if i == 0:
            func = importlib.import_module(s)
        func = getattr(func, s)

    assert callable(func), op + " can not be loaded through custom_op_wrapper"

    # convert any kwarg-only arguments to kwargs
    kwargs = dict()
    # pyrefly: ignore [missing-attribute]
    for func_arg, conv_arg in zip(func._schema.arguments, converted_args):
        if func_arg.kwarg_only:
            kwargs[func_arg.name] = conv_arg
    if kwargs:
        del converted_args[-len(kwargs) :]

    result = func(*converted_args, **kwargs)
    if result is None:
        return None

    if isinstance(result, (list, tuple)):
        # unsafe_alloc_void_ptrs_from_tensors expects result contains tensor only
        result = [torch.tensor([]) if r is None else r for r in result]
        for r in result:
            assert isinstance(r, torch.Tensor), op + " returns a list of non-tensors"
        return torch._C._aoti.unsafe_alloc_void_ptrs_from_tensors(result)  # type: ignore[arg-type]

    assert isinstance(result, torch.Tensor), op + " returns a non-tensor"
    return torch._C._aoti.unsafe_alloc_void_ptr_from_tensor(result)
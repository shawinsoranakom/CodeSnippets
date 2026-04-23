def static_dispatch(
    sig: CppSignature | DispatcherSignature,
    f: NativeFunction,
    backend_indices: list[BackendIndex],
) -> str:
    """
    For a given `NativeFunction`, find out the corresponding backend and dispatch to it. If more than one
    backends exist, fallback to static dispatch by determining dispatch key from inputs.
    Arguments:
        sig: A CppSignature or DispatcherSignature for this native function we want to use.
        f: NativeFunction to generate static dispatch.
        backend_indices: All available backends.
    Return:
        C++ code to call backend-specific functions, e.g., "return at::cpu::add(self, other, scale);"
    """
    if len(backend_indices) == 0 or f.manual_kernel_registration:
        return ""

    keys = [
        b
        for b in backend_indices
        if b.has_kernel(f)
        or (
            f.structured_delegate is not None
            and b.dispatch_key in STRUCTURED_DISPATCH_KEYS
        )
    ]
    if len(keys) == 1:
        return generate_static_dispatch_backend_call(sig, f, keys[0])
    elif len(keys) == 0:
        return generate_static_dispatch_fallback_call(sig, f, backend_indices)

    native_tensor_args = [
        a.name
        for a in sig.arguments()
        if isinstance(a.argument, SelfArgument)
        or isinstance(a.argument, Argument)
        and a.argument.type.is_tensor_like()
    ]
    tensor_args = ", ".join(native_tensor_args)
    tensor_opts = f.func.arguments.tensor_options

    stmts = []
    subexprs: list[str] = []
    if tensor_opts is not None:
        subexprs.append(
            "DispatchKeySet(c10::computeDispatchKey(dtype, layout, device))"
        )
    if tensor_args != "":
        subexprs.append(f"c10::detail::multi_dispatch_key_set({tensor_args})")
    stmts.append(f"""DispatchKeySet _dk_set = {" | ".join(subexprs)};""")
    stmts.append("DispatchKey _dk = c10::highestPriorityBackendTypeId(_dk_set);")

    dispatch_code = []
    for index in keys:
        dispatch_code.append(f"""case DispatchKey::{index.dispatch_key}:""")
        dispatch_code.append(
            f"""\t{generate_static_dispatch_backend_call(sig, f, index)};"""
        )

    fallback = generate_static_dispatch_fallback_call(sig, f, backend_indices)
    connector = "\n\t\t"

    return f"""
    {connector.join(stmts)}
    switch (_dk) {{
        {connector.join(dispatch_code)}
        default:
            {fallback}
    }}
    """
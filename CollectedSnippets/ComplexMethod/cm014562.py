def get_backend_index_for_aoti(
    func: NativeFunction,
    func_group_mapping: dict[OperatorName, NativeFunctionsGroup],
    dispatch_key: DispatchKey | None,
    backend_indices: dict[DispatchKey, BackendIndex],
    extend_aoti_c_shim: bool,
) -> BackendIndex | None:
    backend_index = None

    if dispatch_key is None:
        return backend_index

    if backend_indices[dispatch_key].has_kernel(func) or (
        func.structured_delegate is not None
        and func.structured_delegate in func_group_mapping
        and backend_indices[dispatch_key].has_kernel(
            func_group_mapping[func.structured_delegate]
        )
    ):
        backend_index = backend_indices[dispatch_key]
    else:
        # for the extend out-of-tree kernels, we don't need to
        # duplicatly create C shim wrappers for other dispatch keys
        if extend_aoti_c_shim:
            return backend_index

        elif backend_indices[DispatchKey.CompositeExplicitAutograd].has_kernel(func):
            # We need to create C shim wrappers for CompositeExplicitAutograd kernels
            backend_index = backend_indices[DispatchKey.CompositeExplicitAutograd]
        elif backend_indices[
            DispatchKey.CompositeExplicitAutogradNonFunctional
        ].has_kernel(func):
            # We need to create C shim wrappers for CompositeExplicitAutogradNonFunctional kernels
            backend_index = backend_indices[
                DispatchKey.CompositeExplicitAutogradNonFunctional
            ]
        elif backend_indices[DispatchKey.CompositeImplicitAutograd].has_kernel(func):
            backend_index = backend_indices[DispatchKey.CompositeImplicitAutograd]

    return backend_index
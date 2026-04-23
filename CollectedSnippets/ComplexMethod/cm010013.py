def resolve_key(op: OperatorBase, k: DispatchKey):  # type: ignore[valid-type]
    # 1. (Direct) operator registration
    if op.has_kernel_for_dispatch_key(k):
        return k
    # 2.1 Use CompositeExplicitAutogradNonFunctional kernel if available
    cand = DispatchKey.CompositeExplicitAutogradNonFunctional
    if (
        k == DispatchKey.Undefined or is_included_in_alias(k, cand)
    ) and op.has_kernel_for_dispatch_key(cand):
        return cand
    # 2.2 Use CompositeExplicitAutograd kernel if available
    cand = DispatchKey.CompositeExplicitAutograd
    if (
        k == DispatchKey.Undefined or is_included_in_alias(k, cand)
    ) and op.has_kernel_for_dispatch_key(cand):
        return cand
    has_backend_kernel = op.has_kernel_for_any_dispatch_key(
        torch._C._dispatch_get_backend_keyset_from_autograd(k)
    ) or op.has_kernel_for_dispatch_key(DispatchKey.CompositeExplicitAutograd)
    # 2.3. Use CompositeImplicitAutograd kernel if available
    cand = DispatchKey.CompositeImplicitAutogradNestedTensor
    if (
        (k != DispatchKey.Undefined and is_included_in_alias(k, cand))
        and op.has_kernel_for_dispatch_key(cand)
        and not has_backend_kernel
    ):
        return cand
    cand = DispatchKey.CompositeImplicitAutograd
    if (
        k == DispatchKey.Undefined or is_included_in_alias(k, cand)
    ) and op.has_kernel_for_dispatch_key(cand):
        if k == DispatchKey.AutogradOther and op.has_kernel_for_any_dispatch_key(
            torch._C._dispatch_autogradother_backends
        ):
            raise RuntimeError("ambiguous autogradother kernel")
        elif not has_backend_kernel:
            return cand
    # 2.4. For autograd backend keys, use kernel from DispatchKey::Autograd if available
    cand = DispatchKey.Autograd
    if is_included_in_alias(k, cand) and op.has_kernel_for_dispatch_key(cand):
        return cand
    # 2.5 Use kernel from DispatchKey::FuncTorchBatchedDecomposition if available
    cand = DispatchKey.FuncTorchBatchedDecomposition
    if is_included_in_alias(k, cand) and op.has_kernel_for_dispatch_key(cand):
        return cand
    # Backend fallback
    if torch._C._dispatch_has_backend_fallback(k):
        # The dispatch key itself will implicitly route to backend fallback.
        # This is probably not great for the pure Python implementation.
        return k
    raise NotImplementedError(f"could not find kernel for {op} at dispatch key {k}")
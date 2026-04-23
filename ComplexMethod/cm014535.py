def generate_static_dispatch_fallback_call(
    sig: CppSignature | DispatcherSignature,
    f: NativeFunction,
    backend_indices: list[BackendIndex],
) -> str:
    cpp_sigs = CppSignatureGroup.from_native_function(
        f, method=False, fallback_binding=False
    )
    if sig.symint and f.func.has_symint():
        cpp_sig = cpp_sigs.symint_signature
    else:
        cpp_sig = cpp_sigs.signature
    if cpp_sig is None:
        raise AssertionError("Expected cpp_sig to be non-None")
    name = cpp_sig.name()
    exprs = translate_args(sig, cpp_sig)
    ns = DEFAULT_KERNEL_NAMESPACE.replace("::native", "")
    if f.has_composite_explicit_autograd_kernel:
        return f"return {ns}::{DispatchKey.CompositeExplicitAutograd.lower()}::{name}({exprs});"
    elif f.has_composite_explicit_autograd_non_functional_kernel:
        return f"return {ns}::{DispatchKey.CompositeExplicitAutogradNonFunctional.lower()}::{name}({exprs});"
    elif f.has_composite_implicit_autograd_kernel:
        return f"return {ns}::{DispatchKey.CompositeImplicitAutograd.lower()}::{name}({exprs});"
    elif f.has_composite_implicit_autograd_nested_tensor_kernel:
        return f"return {ns}::{DispatchKey.CompositeImplicitAutogradNestedTensor.lower()}::{name}({exprs});"
    else:
        return f"""TORCH_CHECK(false, "Static dispatch does not support {name} for\
{", ".join([str(index.dispatch_key) for index in backend_indices])} ");"""
def gen_functionalization_registration(
    selector: SelectiveBuilder,
    g: NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup,
    composite_implicit_autograd_index: BackendIndex,
) -> list[str]:
    @with_native_function
    def emit_registration_helper(f: NativeFunction) -> str:
        if f.has_composite_implicit_autograd_kernel:
            metadata = composite_implicit_autograd_index.get_kernel(f)
            if metadata is None:
                raise AssertionError(
                    f"Expected metadata for composite implicit autograd kernel: {f.func}"
                )
            native_api_name = metadata.kernel
            sig = NativeSignature(f.func, symint=metadata.supports_symint())
            # Note [Composite view ops in the functionalization pass]
            # We don't need to worry about implemententing functionalization kernels for views with
            # CompositeImplicitAutograd kernels, because we can just decompose them into their base operators.
            # We can't just opt the entire Functionalization dispatch key into the composite keyset though,
            # because we don't want to decompose non-view ops that are composite, like `at::ones`.
            registration_str = (
                f"static_cast<{sig.ptr_type()}>(at::native::{native_api_name})"
            )
        else:
            # non-composite view ops (and inplace ops) get a normal registration.
            registration_str = f"TORCH_FN(functionalization::{wrapper_name(f.func)})"
        return f'm.impl("{f.func.name}", {registration_str});'

    # Don't generate kernels in mobile build
    if not selector.include_all_operators:
        return []

    if isinstance(g, NativeFunctionsViewGroup):
        # functionalization needs to register kernels for view + view_inplace ops
        # See Note [Functionalization <> torch.Tensor constructor]
        if str(g.view.func.name) == "lift_fresh":
            return []
        view_str = []
        view_str.append(emit_registration_helper(g.view))
        if g.view_inplace is not None:
            if not g.view_inplace.is_view_op:
                raise AssertionError(
                    f"Expected view_inplace to be a view op: {g.view_inplace.func}"
                )
            view_str.append(emit_registration_helper(g.view_inplace))
        return view_str

    elif isinstance(g, NativeFunctionsGroup):
        # Gets a hand-written functionalization kernel
        if g.inplace is not None and str(g.inplace.func.name) == "set_.source_Tensor":
            fns = []
        else:
            fns = list(g.functions())
    else:
        if str(g.func.name) in MUTABLE_OPS_NOT_USING_FUNCTIONALIZATION:
            return []
        fns = [g]

    registrations = []
    for f in fns:
        if f.has_composite_implicit_autograd_kernel:
            continue
        if str(f.func.name) == "lift":
            # See Note [Functionalization <> torch.Tensor constructor]
            return []
        if str(f.func.name) == "resize_":
            # See Note [resize_ in Functionalization]
            return []
        if str(f.func.name.name) != "set_":
            if f.is_view_op:
                raise AssertionError(f"Unexpected view op: {f.func}")
        # functionalization needs to generate and register kernels for inplace ops.
        # We *also* need to directly register CompositeImplicitAUtograd kernels
        # so that they decompose properly before functioanlization.
        if modifies_arguments(f):
            registrations.append(emit_registration_helper(f))
    return registrations
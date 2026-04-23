def generate_function(
    f: NativeFunction, k: SchemaKind
) -> tuple[NativeFunction, dict[DispatchKey, dict[OperatorName, BackendMetadata]]]:
    from torchgen.api import cpp

    if k == SchemaKind.functional:
        if f.func.kind() == SchemaKind.functional:
            raise AssertionError("Cannot generate functional from functional schema")
        # The new "functional" NativeFunction has:
        # - any mutable arguments have been converted into (immutable) returns.
        #   (if a mutable argument was not also a return, it gets converted to one)
        # - "_functional" appended to the base name, ONLY IF this op has a mutable variant.
        #   See Note [Overload Ambiguity With Functional Variants]
        # The default grouping logic in signature() actually already does this,
        # so we can piggy-back off it (but we still want return names)
        func = f.func.signature(keep_return_names=True).with_name(
            OperatorName(
                name=BaseOperatorName(
                    base=f.func.name.name.base,
                    inplace=False,
                    dunder_method=f.func.name.name.dunder_method,
                    # See Note [Overload Ambiguity With Functional Variants]
                    functional_overload=f.func.kind() == SchemaKind.mutable,
                ),
                overload_name=f.func.name.overload_name,
            )
        )
    elif k == SchemaKind.out:
        # We generate out= ops mostly just so that we can pair up NativeFunctions into groups easily,
        # but at least today, there is no good reason to actually use them.
        # we'll generate a dispatcher entry for them, but won't actually register any kernels for them.
        if f.func.kind() == SchemaKind.inplace:
            func = self_to_out_signature(f.func)
        elif f.func.kind() == SchemaKind.mutable:
            func = mutable_to_out_signature(f.func)
        elif f.func.kind() == SchemaKind.functional:
            func = functional_to_out_signature(f.func)
        else:
            raise AssertionError(
                "We only bother generating out= functions from either inplace or mutable or functional variants"
            )
    else:
        raise AssertionError(
            "We currently only generate either functional or out= NativeFunctions"
        )

    # Generated kernel naming convention for out: <op_name>_<overload_name>. The reason for this is to
    # disambiguate operator with the same name but different overload name, e.g., `randn.names_out` and
    # `randn.generator_with_names_out`.
    kernel_name = (
        func.name.unambiguous_name()
        if func.kind() == SchemaKind.out
        else cpp.name(func)
    )
    if f.func.has_symint():
        kernel_name += "_symint"
    backend_metadata = {
        DispatchKey.CompositeExplicitAutograd: {
            func.name: BackendMetadata(
                kernel=kernel_name,
                structured=False,
                cpp_namespace=DEFAULT_KERNEL_NAMESPACE,
            )
        }
    }
    tags = {"generated"} | set(
        f.tags & {"nondeterministic_seeded", "view_copy", "pt2_compliant_tag"}
    )
    if func.is_out_fn():
        tags.add("out")

    return (
        NativeFunction(
            func=func,
            use_const_ref_for_mutable_tensors=f.use_const_ref_for_mutable_tensors,
            # These generated fn's aren't meant to be user friendly- don't generate methods.
            variants={Variant.function},
            structured=False,
            structured_delegate=None,
            structured_inherits=None,
            precomputed=None,
            autogen=[],
            ufunc_inner_loop={},
            manual_kernel_registration=False,
            manual_cpp_binding=False,
            python_module=None,
            category_override=None,
            device_guard=False,
            device_check=DeviceCheckType.NoCheck,
            loc=f.loc,
            cpp_no_default_args=set(),
            is_abstract=f.is_abstract,
            has_composite_implicit_autograd_kernel=False,
            has_composite_implicit_autograd_nested_tensor_kernel=False,
            has_composite_explicit_autograd_kernel=True,
            has_composite_explicit_autograd_non_functional_kernel=False,
            # Every generated NativeFunction gets a "generated" tag, so it's easy to tell
            # which NativeFunction objects did not come directly from native_functions.yaml.
            tags=tags,
            namespace=f.namespace,
        ),
        backend_metadata,
    )
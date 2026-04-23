def emit_call(
        f: NativeFunction, unpacked_bindings: list[Binding], try_jit_decomposition: bool
    ) -> str:
        # We only care about adding `at::AutoDispatchBelowAutograd` guard for non-variable dispatch
        # (which corresponds to 'use_derived' strategy). The purpose of this guard is to make sure
        # the baseType operations still dispatch to non-Variable type, even if the arguments passed
        # in are now Variables.
        # See NOTE [ Treating Variables as non-Variables in type dispatch ] for details.
        unpacked_args = [b.name for b in unpacked_bindings]
        base_type_call = emit_dispatch_call(f, "self_", unpacked_args)

        if get_view_info(f) is not None or modifies_arguments(f):
            guard = "at::AutoDispatchBelowAutograd guard;"
        else:
            guard = "at::AutoDispatchBelowADInplaceOrView guard;"

        any_has_forward_grad = (
            get_any_has_fw_grad_cond(derivative=None)
            if requires_derivative
            else "false"
        )
        return_types = ", ".join(
            [cpp.return_type(a, symint=True).cpp_type() for a in f.func.returns]
        )
        if len(f.func.returns) > 1:
            return_types = f"std::tuple<{return_types}>"

        arg_names = [
            a.name
            for a in cpp.arguments(
                f.func.arguments,
                faithful=True,
                symint=True,
                method=False,
                cpp_no_default_args=set(),
            )
        ]

        if not modifies_arguments(f) and not returns_void:
            if try_jit_decomposition:
                call = DISPATCH_TO_NON_VAR_TYPE_WITH_TMP_RETURN_VALUES_JVP_DECOMP.substitute(
                    base_type_call=base_type_call,
                    tmp_var=TMP_VAR,
                    guard=guard,
                    any_has_forward_grad=any_has_forward_grad,
                    op_name=cpp.name(f.func),
                    op_overload=f.func.name.overload_name,
                    return_types=return_types,
                    arg_names=arg_names,
                )
            else:
                call = DISPATCH_TO_NON_VAR_TYPE_WITH_TMP_RETURN_VALUES.substitute(
                    base_type_call=base_type_call,
                    tmp_var=TMP_VAR,
                    guard=guard,
                )

            call += wrap_output(f, unpacked_bindings, TMP_VAR)
        else:
            if try_jit_decomposition:
                raise AssertionError(
                    "try_jit_decomposition should be False for functions with no return values or that modify arguments"
                )
            call = DISPATCH_TO_NON_VAR_TYPE_WITHOUT_RETURN_VALUES.substitute(
                base_type_call=base_type_call, guard=guard
            )
        call = check_tensorimpl_and_storage(call, unpacked_bindings)
        return call
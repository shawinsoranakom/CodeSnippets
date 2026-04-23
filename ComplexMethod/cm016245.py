def check_tensorimpl_and_storage(
        call: str, unpacked_bindings: list[Binding]
    ) -> str:
        # See NOTE [ TensorImpl and Storage Pointer Sanity Checks ]
        stmts_before_call: list[str] = []
        stmts_after_call: list[str] = []

        if cpp.name(f.func) in DONT_ENFORCE_SAME_TENSOR_IMPL_OR_STORAGE:
            return call

        # Check properties of inputs (enforce (1))
        for unpacked_binding in unpacked_bindings:
            arg = unpacked_binding.name
            noref_cpp_type = unpacked_binding.nctype.type.remove_const_ref()
            if noref_cpp_type == BaseCType(tensorListT) or noref_cpp_type == BaseCType(
                iTensorListRefT
            ):
                stmts_before_call += [
                    SAVE_TENSORLIST_STORAGE.substitute(tensorlist_name=arg),
                    SAVE_TENSORLIST_IMPL.substitute(tensorlist_name=arg),
                ]
                stmts_after_call += [
                    ENFORCE_SAME_TENSORLIST_STORAGE.substitute(tensorlist_name=arg),
                    ENFORCE_SAME_TENSORLIST_IMPL.substitute(tensorlist_name=arg),
                ]
            elif noref_cpp_type == ListCType(OptionalCType(BaseCType(tensorT))):
                stmts_before_call += [
                    SAVE_OPTIONALTENSORLIST_STORAGE.substitute(tensorlist_name=arg),
                    SAVE_OPTIONALTENSORLIST_IMPL.substitute(tensorlist_name=arg),
                ]
                stmts_after_call += [
                    ENFORCE_SAME_OPTIONALTENSORLIST_STORAGE.substitute(
                        tensorlist_name=arg
                    ),
                    ENFORCE_SAME_OPTIONALTENSORLIST_IMPL.substitute(
                        tensorlist_name=arg
                    ),
                ]
            elif noref_cpp_type == BaseCType(tensorT):
                stmts_before_call += [
                    SAVE_TENSOR_STORAGE.substitute(tensor_name=arg),
                    SAVE_TENSOR_IMPL.substitute(tensor_name=arg),
                ]
                stmts_after_call += [
                    ENFORCE_SAME_TENSOR_STORAGE.substitute(
                        tensor_name=arg, out_tensor_name=arg
                    ),
                    ENFORCE_SAME_TENSOR_IMPL.substitute(tensor_name=arg),
                ]

        if not (
            (stmts_before_call and stmts_after_call)
            or (not stmts_before_call and not stmts_after_call)
        ):
            raise AssertionError(
                "stmts_before_call and stmts_after_call must be both empty or both non-empty"
            )

        # Check properties of outputs (enforce (2), (3))
        if f.func.kind() not in (SchemaKind.inplace, SchemaKind.out):
            base_name = f.func.name.name.base  # TODO: should be str(f.func.name.name)?
            aliased_arg_name = ALL_VIEW_FUNCTIONS.get(base_name, None)
            if aliased_arg_name is not None:
                aliased_arg_name = unpacked_name(aliased_arg_name)
            for i, (ret, ret_name) in enumerate(
                zip(f.func.returns, cpp.return_names(f))
            ):
                noref_cpp_type = cpp.return_type(ret, symint=True).remove_const_ref()
                if noref_cpp_type == BaseCType(tensorT):
                    if aliased_arg_name is not None:
                        if i != 0:
                            raise AssertionError(
                                f"Expect non-CompositeImplicitAutograd view function {base_name} "
                                f"to return single output, got index {i}"
                            )
                        stmts_after_call += [
                            ENFORCE_SAME_TENSOR_STORAGE.substitute(
                                tensor_name=aliased_arg_name, out_tensor_name=ret_name
                            )
                        ]
                    else:
                        if (
                            type_wrapper_name(f)
                            not in DONT_ENFORCE_STORAGE_IMPL_USE_COUNT
                        ):
                            stmts_after_call += [
                                ENFORCE_TENSOR_STORAGE_USE_COUNT_EQUALS_ONE.substitute(
                                    tensor_name=ret_name, fn_name=type_wrapper_name(f)
                                )
                            ]

                    if type_wrapper_name(f) not in DONT_ENFORCE_TENSOR_IMPL_USE_COUNT:
                        stmts_after_call += [
                            ENFORCE_TENSOR_IMPL_USE_COUNT.substitute(
                                tensor_name=ret_name, fn_name=type_wrapper_name(f)
                            )
                        ]

                # Currently we don't have any functions that return the following types, but
                # we should update the checks once we do
                elif noref_cpp_type == ListCType(OptionalCType(BaseCType(tensorT))):
                    raise AssertionError(
                        f"Please add use_count checks for {noref_cpp_type}"
                    )
                elif noref_cpp_type == BaseCType(tensorListT):
                    raise AssertionError(
                        f"Please add use_count checks for {noref_cpp_type}"
                    )

        if stmts_before_call and stmts_after_call:
            call = (
                RUN_ONLY_IN_DEBUG_MODE.substitute(statements=stmts_before_call)
                + call
                + RUN_ONLY_IN_DEBUG_MODE.substitute(statements=stmts_after_call)
            )
        return call
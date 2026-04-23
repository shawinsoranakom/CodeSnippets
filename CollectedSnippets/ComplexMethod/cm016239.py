def emit_body(
    fn: NativeFunctionWithDifferentiabilityInfo, key: str = "Default"
) -> list[str]:
    if dispatch_strategy(fn) != "use_derived":
        raise AssertionError(
            f"dispatch_strategy(fn) is {dispatch_strategy(fn)}, expected 'use_derived'"
        )
    f = fn.func
    info = fn.info[key] if fn.info else None
    fw_derivatives = fn.fw_derivatives.get(key, []) if fn.fw_derivatives else []

    name = cpp.name(f.func)
    inplace = f.func.kind() == SchemaKind.inplace
    is_out_fn = f.func.kind() == SchemaKind.out
    returns_void = len(f.func.returns) == 0
    base_name = get_base_name(f)
    view_info = get_view_info(f)

    is_foreach = name.startswith("_foreach")
    is_inplace_foreach = is_foreach and inplace
    if is_inplace_foreach:
        inplace_foreacharg2refarg: dict[Argument, Argument] = {}
        refargname2inplace_foreacharg: dict[str, Argument] = {}
        base_name_and_overload_name = (f.func.name.name.base, f.func.name.overload_name)
        if info is None:
            if (
                base_name_and_overload_name
                not in _foreach_ops_without_differentiability_info
            ):
                raise AssertionError(
                    f"{'.'.join(base_name_and_overload_name)} should have a differentiability info"
                )
        else:
            if not (
                len(f.func.arguments.flat_non_out)
                == len(info.func.func.arguments.flat_non_out)
            ) and (
                base_name_and_overload_name not in _foreach_ops_with_different_arity
            ):
                raise AssertionError(
                    f"{'.'.join(base_name_and_overload_name)} has {len(f.func.arguments.flat_non_out)} args "
                    f"but the reference has {len(info.func.func.arguments.flat_non_out)}"
                )
            for foreach_arg, ref_arg in zip(
                f.func.arguments.flat_non_out, info.func.func.arguments.flat_non_out
            ):
                foreach_arg_type = foreach_arg.type
                if isinstance(foreach_arg_type, ListType):
                    foreach_arg_type = foreach_arg_type.elem
                if foreach_arg_type != ref_arg.type:
                    raise AssertionError(
                        f"foreach_arg_type ({foreach_arg_type}) != ref_arg.type ({ref_arg.type})"
                    )
                inplace_foreacharg2refarg[foreach_arg] = ref_arg
                refargname2inplace_foreacharg[ref_arg.name] = foreach_arg

    def gen_differentiable_input(
        arg: Argument | SelfArgument | TensorOptionsArguments,
    ) -> DifferentiableInput | None:
        if isinstance(arg, TensorOptionsArguments):
            return None
        a: Argument = arg.argument if isinstance(arg, SelfArgument) else arg

        # TODO: `cpp_type` is only to keep it byte-for-byte compatible with the old codegen, should remove.
        # NB: This is not a clone of cpp.argument() - TensorOptionsArguments / faithful / binds are
        # not handled properly as they are irrelevant for this codegen.
        cpp_type = cpp.argument_type(a, binds=a.name, symint=True).cpp_type()

        if not is_differentiable(a.name, a.type, info):
            return None
        return DifferentiableInput(
            name=a.name,
            type=a.type,
            cpp_type=cpp_type,
        )

    @with_native_function
    def gen_differentiable_inputs(f: NativeFunction) -> list[DifferentiableInput]:
        arguments = list(f.func.arguments.non_out)
        if is_inplace_foreach and info is not None:
            for i, arg in enumerate(f.func.arguments.flat_non_out):
                if arg in inplace_foreacharg2refarg:
                    # note(crcrpar): From what I understand, what matters is only the name.
                    # Thus originally I only replace argument only when the names are different.
                    # TODO(crcrpar): Make it simpler.
                    mapped_arg = inplace_foreacharg2refarg[arg]
                    arguments[i] = Argument(
                        mapped_arg.name,
                        mapped_arg.type,
                        mapped_arg.default,
                        mapped_arg.annotation,
                    )
        return list(mapMaybe(gen_differentiable_input, arguments))

    def find_args_with_derivatives(
        differentiable_inputs: list[DifferentiableInput],
    ) -> list[DifferentiableInput]:
        """Find arguments that have derivative definitions"""
        if info is None or not info.has_derivatives:
            return differentiable_inputs
        names = {name for d in info.derivatives for name in d.var_names}
        differentiable = [arg for arg in differentiable_inputs if arg.name in names]
        if len(differentiable) != len(names):
            missing = names - {arg.name for arg in differentiable}
            raise RuntimeError(
                f"Missing arguments for derivatives: {missing} in {info.name}"
            )
        return differentiable

    differentiable_inputs = gen_differentiable_inputs(f)
    args_with_derivatives = find_args_with_derivatives(differentiable_inputs)
    differentiable_outputs = gen_differentiable_outputs(fn, key)

    undifferentiable = (base_name in DONT_REQUIRE_DERIVATIVE) or (
        name in DONT_REQUIRE_DERIVATIVE
    )

    requires_derivative = (
        (not undifferentiable)
        and (len(differentiable_inputs) > 0)
        and (
            (len(differentiable_outputs) > 0)
            # note(crcrpar): In-place foreach functions are a void function.
            or is_inplace_foreach
        )
    )

    if (
        info is not None
        and info.has_derivatives
        and not requires_derivative
        # out= ops are allowed to have zero returns which cause requires_derivative to be False
        # we shouldn't error out though (out= ops for autograd just redispatch)
        and len(f.func.returns) > 0
    ):
        raise RuntimeError(
            f"ERROR: derivative ignored for {name} -- specified an autograd function without derivative"
        )

    # note(crcrpar): In-place foreach functions do not support forward AD
    if requires_derivative and len(fw_derivatives) > 0 and not is_inplace_foreach:
        num_fw_derivative_var_names = sum(
            len(derivative.var_names) for derivative in fw_derivatives
        )
        if num_fw_derivative_var_names != len(differentiable_outputs):
            raise AssertionError(
                f"Expected the number of forward derivatives implemented ({num_fw_derivative_var_names}) to match the "
                f"number of differentiable outputs ({len(differentiable_outputs)}). NB: This only applies when at least "
                "one forward derivative is implemented. Not implementing any forward "
                "derivatives is also okay, and we would require inputs to the op to "
                "not have associated tangents in that case."
            )

    try_jit_decomposition = (
        requires_derivative
        and len(fw_derivatives) == 0
        and (not modifies_arguments(f))
        and (not returns_void)
    )

    def emit_save_inputs() -> list[str]:
        setup: list[str] = []
        if info is None or not info.has_derivatives:
            return setup

        has_tensorlist_arg = any(
            is_tensor_list_type(arg.type) for arg in args_with_derivatives
        )

        # We don't want to save tensors if we know that they will never be used
        # when computing the derivative, so we add guards to those statements
        def guard_for(arg: SavedAttribute) -> str | None:
            if info is None:
                raise AssertionError("info is None in guard_for")

            # It's hard to determine the edge offset if we have TensorLists
            # NOTE(crcrpar): in-place foreach functions' arguments include tensorlist
            # but their derivatives don't use it, so let them bypass this check.
            if has_tensorlist_arg and (not is_inplace_foreach):
                return None

            # Empirical evaluation of the cases where we insert those guards in
            # backward show that they are somewhat useless. E.g. there's no need
            # to guard on some values captured from forward, because they had to
            # require_grad if the backward function even gets executed. I don't
            # have any good ideas for detecting those cases, so I simply disabled the
            # checks.
            if "backward" in info.name:
                return None

            # If there's a single derivative we could compute, we already have
            # a requires_grad check that is sufficient
            if len(args_with_derivatives) <= 1:
                return None

            # We really only care about trimming down the amount of tensors we save
            if arg.nctype.type != BaseCType(tensorT):
                return None

            # We want to emit simple guards, so we only allow that if checking one
            # input is enough to determine whether we need that value
            used_in = [d for d in info.derivatives if arg in d.saved_inputs]
            if len(used_in) == 0:
                raise AssertionError(f"used_in is empty for arg {arg.nctype.name}")
            if len(used_in) != 1:
                return None
            derivative = used_in[0]

            # Case with multioutput formulas
            # TODO: process all derivative formulas!!!
            if len(derivative.var_names) != 1:
                wrap_opt_if_start = derivative.formula.find(
                    f"wrap_opt_if({arg.nctype.name}"
                )
                if wrap_opt_if_start == -1:
                    return None

                wrap_opt_if_match = re.match(
                    rf"wrap_opt_if\({arg.nctype.name},(.*?)\)",
                    derivative.formula[wrap_opt_if_start:],
                )
                if wrap_opt_if_match is None:
                    raise AssertionError(
                        f"wrap_opt_if_match is None for {arg.nctype.name} in {derivative.formula}"
                    )

                # Condition is between 'wrap_opt_if(var_name,' and ')'.
                condition_slice = slice(len(rf"wrap_opt_if\({arg.nctype.name},"), -1)
                wrap_opt_if_condition = wrap_opt_if_match.group(0)[
                    condition_slice
                ].strip()
                # replace 'grad_input_mask[num]' with 'grad_fn->should_compute_output(num)'
                wrap_opt_if_condition = re.sub(
                    r"grad_input_mask\[(\d+)\]",
                    r"grad_fn->should_compute_output(\1)",
                    wrap_opt_if_condition,
                )
                return f"{wrap_opt_if_condition}"

            # Figure out the offset of the edge that uses this variable
            derivative_var_name = derivative.var_names[0]
            for edge_off, a in enumerate(args_with_derivatives):
                if a.name == derivative_var_name:
                    break
            else:
                raise AssertionError
            return f"grad_fn->should_compute_output({edge_off})"

        if is_inplace_foreach:
            save_input_stmts = save_variables(info.all_saved_inputs, False, guard_for)
            if save_input_stmts:
                setup.append(
                    LOOP_OVER_VECTOR_OF_GRAD_FNS.substitute(
                        preamble="", statements=save_input_stmts
                    )
                )
        else:
            setup.extend(save_variables(info.all_saved_inputs, False, guard_for))
            for arg in args_with_derivatives:
                if is_tensor_list_type(arg.type):
                    setup.append(f"grad_fn->{arg.name}_size_ = {arg.name}.size();")
        return setup

    def setup_derivative(differentiable_inputs: list[DifferentiableInput]) -> list[str]:
        body: list[str] = []
        if is_out_fn:
            # For out functions, ensure that no input or output requires grad
            body.append(DECLARE_GRAD_FN.substitute(op="Node"))
            body.append(
                SETUP_NONE_REQUIRES_GRAD.substitute(
                    base_name=base_name,
                    args_to_check=[arg.name for arg in differentiable_inputs],
                )
            )
            body.append(
                SETUP_NONE_REQUIRES_GRAD.substitute(
                    base_name=base_name,
                    args_to_check=[arg.name for arg in differentiable_outputs],
                )
            )
            return body

        op = info.op if info is not None and info.has_derivatives else "NotImplemented"
        setup = []
        if not is_inplace_foreach:
            setup.extend(
                ASSIGN_GRAD_FN.substitute(
                    op=op,
                    op_ctor=""
                    if info is not None and info.has_derivatives
                    else f'"{cpp.name(f.func)}"',
                    args_with_derivatives=[arg.name for arg in args_with_derivatives],
                ).split("\n")
            )
        else:
            # note(crcrpar): Assuming in-place foreach function's self_arg is always TensorList.
            list_like_arg = "self"
            args = [arg.name for arg in args_with_derivatives]
            for i, arg in enumerate(args):
                if is_inplace_foreach and info is not None:
                    if arg in refargname2inplace_foreacharg:
                        foreach_arg = refargname2inplace_foreacharg[arg]
                        args[i] = foreach_arg.name + (
                            "[i]" if isinstance(foreach_arg.type, ListType) else ""
                        )
                else:
                    if arg == list_like_arg:
                        args[i] = arg + "[i]"
            setup.extend(
                ASSIGN_VECTOR_OF_GRAD_FN.substitute(
                    op=op,
                    op_ctor=""
                    if info is not None and info.has_derivatives
                    else f'"{cpp.name(f.func)}"',
                    args_with_derivatives=args,
                    irange=f"{list_like_arg}.size()",
                ).split("\n")
            )
        setup.extend(emit_save_inputs())

        body.extend(
            emit_check_no_requires_grad(differentiable_inputs, args_with_derivatives)
        )
        declare_grad_fn_template = (
            DECLARE_GRAD_FN if not is_inplace_foreach else DECLARE_VECTOR_OF_GRAD_FN
        )
        body.append(declare_grad_fn_template.substitute(op=op))
        body.append(SETUP_DERIVATIVE.substitute(setup=setup))
        return body

    def emit_check_if_in_complex_autograd_allowlist() -> list[str]:
        body: list[str] = []
        if base_name in GRADIENT_IMPLEMENTED_FOR_COMPLEX:
            return body
        for arg in differentiable_outputs:
            name = arg.name
            # TODO: should be `arg.type.is_tensor_like()`?
            if arg.cpp_type == "at::Tensor" or arg.cpp_type in TENSOR_LIST_LIKE_CTYPES:
                body.append(f'throw_error_for_complex_autograd({name}, "{base_name}");')
        return body

    def emit_check_no_requires_grad(
        tensor_args: list[DifferentiableInput],
        args_with_derivatives: list[DifferentiableInput],
    ) -> list[str]:
        """Checks that arguments without derivatives don't require grad"""
        body: list[str] = []
        for arg in tensor_args:
            if arg in args_with_derivatives:
                continue
            arg_name = arg.name
            if info and arg_name in info.non_differentiable_arg_names:
                continue
            if arg_name == "output":
                # Double-backwards definitions sometimes take in 'input' and
                # 'output', but only define the derivative for input.
                continue
            body.append(f'check_no_requires_grad({arg_name}, "{arg_name}", "{name}");')
        return body

    def emit_original_self_definition() -> list[str]:
        body: list[str] = []
        if inplace:
            if is_inplace_foreach:
                body.append(
                    "std::vector<::std::optional<at::Tensor>> original_selfs(self.size());"
                )
            else:
                body.append("::std::optional<at::Tensor> original_self;")

            all_forward_grad_cond = []
            for derivative in fw_derivatives:
                if derivative.required_original_self_value:
                    all_forward_grad_cond.append(
                        get_any_has_forward_grad_name(derivative.var_names)
                    )

            if all_forward_grad_cond:
                if not is_inplace_foreach:
                    body.append(f"if ({' || '.join(all_forward_grad_cond)}) {{")
                    body.append("  original_self = self.clone();")
                    body.append("}")
                else:
                    current_all_forward_grad_cond = [
                        f"{cond}[i]" for cond in all_forward_grad_cond
                    ]
                    body.append("for (const auto& i : c10::irange(self.size())) {")
                    body.append(
                        f"  if ({' || '.join(current_all_forward_grad_cond)}) {{"
                    )
                    body.append("    original_selfs[i] = self[i].clone();")
                    body.append("  }")
                    body.append("}")

        return body

    def save_variables(
        saved_variables: Sequence[SavedAttribute],
        is_output: bool,
        guard_for: Callable[[SavedAttribute], str | None] = lambda name: None,
    ) -> Sequence[str]:
        # assign the saved variables to the generated grad_fn
        stmts: list[str] = []
        for arg in sorted(saved_variables, key=lambda sa: str(sa.nctype.name)):
            name = (
                arg.nctype.name.name
                if isinstance(arg.nctype.name, SpecialArgName)
                else arg.nctype.name
            )
            foreacharg: Argument | None = None
            is_foreacharg_list_type: bool = False
            type = arg.nctype.type
            expr = arg.expr
            stmts_prepend = None
            if is_inplace_foreach and info is not None:
                # todo(crcrpar): See if we can add some check e.g. `assert foreacharg is not None`.
                # for now the example assert would fail.
                name_to_query = name.split("_scalar_type")[0]
                if name_to_query in refargname2inplace_foreacharg:
                    foreacharg = refargname2inplace_foreacharg[name_to_query]
                    is_foreacharg_list_type = isinstance(foreacharg.type, ListType)
                if foreacharg is not None:
                    name_in_expr = (
                        f"{foreacharg.name}{'[i]' if is_foreacharg_list_type else ''}"
                    )
                    src_name = name
                    if "_scalar_type" in src_name:
                        split_src_name = src_name.split("_scalar_type")
                        if len(split_src_name) != 2:
                            raise AssertionError(
                                f"expected 2 parts after split, got {len(split_src_name)}: {split_src_name}"
                            )
                        src_name = split_src_name[0]
                    expr = expr.replace(src_name, name_in_expr)
            if (
                type == BaseCType(tensorT)
                or type == OptionalCType(BaseCType(tensorT))
                or type == MutRefCType(OptionalCType(BaseCType(tensorT)))
                or (is_output and type == BaseCType(scalarT))
            ):
                # note(crcrpar): Here `expr` is generated from scratch, `arg.expr` is ignored.
                var = name
                name += "_"
                if var == "self" and inplace:
                    original_self_var = (
                        "original_self"
                        if not is_inplace_foreach
                        else "original_selfs[i]"
                    )
                    self_var = var if not is_inplace_foreach else var + "[i]"
                    stmts_prepend = f"if (!{original_self_var}.has_value()) {original_self_var} = {self_var}.clone()"
                    var = f"{original_self_var}.value()"
                    if is_output:
                        raise AssertionError(
                            "is_output should be False when var == 'self' and inplace"
                        )
                if inplace and is_output:
                    if name != "result_":
                        raise AssertionError(
                            f"expected name to be 'result_' for inplace output, got {name}"
                        )
                    var = (
                        "self[i]"
                        if is_inplace_foreach or is_foreacharg_list_type
                        else "self"
                    )
                    is_inplace_view = f"{var}.is_view()"
                    expr = f"SavedVariable({var}, {str(is_output).lower()}, {is_inplace_view})"
                else:
                    expr = f"SavedVariable({var}, {str(is_output).lower()})"
                    if foreacharg is not None and "original_selfs" not in expr:
                        # pyrefly: ignore [unbound-name]
                        expr = expr.replace(src_name, name_in_expr)
            elif (
                type == BaseCType(tensorListT)
                or type == ListCType(OptionalCType(BaseCType(tensorT)))
                or type == BaseCType(iTensorListRefT)
                or type == VectorCType(BaseCType(tensorT))
            ):
                # See Note [nuanced return type of out-of-place foreach functions]
                if type == VectorCType(BaseCType(tensorT)):
                    if not (is_foreach and is_output):
                        raise AssertionError(
                            f"VectorCType(BaseCType(tensorT)) requires is_foreach and is_output, "
                            f"got is_foreach={is_foreach}, is_output={is_output}"
                        )
                expr = f"make_saved_variable_list({name}, {str(is_foreach and is_output).lower()})"
                name += "_"
            elif type == BaseCType(intArrayRefT):
                expr = expr + ".vec()"
            elif type == BaseCType(symIntArrayRefT):
                expr = expr + ".vec()"
            elif type == BaseCType(stringT):
                expr = f"std::string({expr})"
            elif type == OptionalCType(BaseCType(stringT)):
                expr = f"{expr}.has_value() ? ::std::optional<std::string>(std::string({expr}.value())) : ::std::nullopt"
            elif type == ArrayRefCType(
                elem=BaseCType(type=BaseCppType(ns="at", name="Scalar"))
            ):
                expr = expr + ".vec()"

            guard = guard_for(arg)
            if guard is None:
                if stmts_prepend:
                    stmts.append(f"{stmts_prepend};")
                stmts.append(f"grad_fn->{name} = {expr};")
            else:
                stmts.append(f"if ({guard}) {{")
                if stmts_prepend:
                    stmts.append(f"  {stmts_prepend};")
                stmts.append(f"  grad_fn->{name} = {expr};")
                stmts.append("}")
        return stmts

    # Generates a Dispatcher::redispatch() call into the dispatcher. We do this mainly for performance reasons:
    #  - Pre-compute the full DispatchKeySet. This saves the dispatcher from having to read from TLS.
    #  - redispatch() avoids a redundant call to RecordFunction, which was already called right before
    #    we entered this autograd kernel.
    def emit_dispatch_call(
        f: NativeFunction, input_base: str, unpacked_args: Sequence[str]
    ) -> str:
        """Dispatch call via function in a namespace or method on Tensor."""
        # code-generated autograd kernels plumb and recompute dispatch keys directly through the kernel for performance.
        # Ops also always have a function variant of the redispatch API.
        # See Note [Plumbing Keys Through The Dispatcher] for details.
        dispatch_key_set = "ks & c10::after_autograd_keyset"
        call = CALL_REDISPATCH.substitute(
            api_name=cpp.name(
                f.func,
                faithful_name_for_out_overloads=True,
                symint_overload=f.func.has_symint(),
            ),
            unpacked_args=[dispatch_key_set] + list(unpacked_args),
        )
        return call

    def wrap_output(
        f: NativeFunction, unpacked_bindings: list[Binding], var: str
    ) -> str:
        call = ""
        rhs_value: str | None = None
        if not any(r.type.is_tensor_like() for r in f.func.returns):
            rhs_value = var
        else:
            rhs_value = f"std::move({var})"
        if rhs_value is None:
            raise AssertionError("rhs_value is None")
        call += ASSIGN_RETURN_VALUE.substitute(
            return_values=tie_return_values(f), rhs_value=rhs_value
        )
        return call

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

    def emit_history() -> str:
        fn = "rebase" if modifies_arguments(f) and view_info is None else "set"
        output_names = [r.name for r in differentiable_outputs]
        # TODO: flatten allocates a std::vector, which could be expensive
        outs = CodeTemplate("flatten_tensor_args( ${outs} )").substitute(
            outs=output_names if not is_inplace_foreach else "self"
        )
        if not is_inplace_foreach:
            return SET_HISTORY.substitute(fn=fn, differentiable_outputs=outs)
        else:
            return LOOP_OVER_VECTOR_OF_GRAD_FNS.substitute(
                preamble=(
                    f"auto differentiable_outputs = {outs};\n"
                    f"TORCH_INTERNAL_ASSERT(differentiable_outputs.size() == grad_fns.size());"
                ),
                statements=f"{fn}_history(differentiable_outputs[i], grad_fns[i]);",
            )

    def emit_save_outputs() -> str:
        if is_out_fn:
            # out functions don't currently support differentiation
            return ""
        if info is not None and info.has_derivatives:
            stmts = save_variables(info.all_saved_outputs, True)
            if len(stmts) == 0:
                return ""
            if not is_inplace_foreach:
                return CONDITIONAL.substitute(cond="grad_fn", statements=stmts)
            else:
                return LOOP_OVER_VECTOR_OF_GRAD_FNS.substitute(
                    preamble="", statements=stmts
                )
        return ""

    def emit_any_requires_grad() -> list[str]:
        extra_condition = ""
        if info and info.output_differentiability_conditions:
            if len(info.output_differentiability_conditions) != 1:
                raise AssertionError(
                    f"expected 1 output_differentiability_condition, got {len(info.output_differentiability_conditions)}"
                )
            extra_condition = f"_any_requires_grad &= ({info.output_differentiability_conditions[0]});"
        names_of_args_with_derivatives = [arg.name for arg in args_with_derivatives]
        if is_inplace_foreach and info is not None:
            for i, arg in enumerate(names_of_args_with_derivatives):
                for f_arg, r_arg in inplace_foreacharg2refarg.items():
                    if arg == r_arg.name:
                        names_of_args_with_derivatives[i] = f_arg.name
        return [
            SETUP_ANY_REQUIRES_GRAD.substitute(
                args_with_derivatives=names_of_args_with_derivatives,
                extra_differentiability_conditions=extra_condition,
            )
        ]

    def get_any_has_forward_grad_name(var_names: tuple[str, ...]) -> str:
        if len(var_names) == 1:
            return f"_any_has_forward_grad_{var_names[0]}"
        else:
            return f"_any_has_forward_grad_{'_'.join(var_names)}"

    def emit_any_has_forward_grad() -> list[str]:
        content: list[str] = []
        if not is_foreach:
            for derivative in fw_derivatives:
                requires_fw_grad = get_any_has_fw_grad_cond(derivative=derivative)
                if info and info.output_differentiability_conditions:
                    if len(info.output_differentiability_conditions) != 1:
                        raise AssertionError(
                            f"expected 1 output_differentiability_condition, got {len(info.output_differentiability_conditions)}"
                        )
                    requires_fw_grad = f"({info.output_differentiability_conditions[0]}) && {requires_fw_grad}"
                content.append(
                    f"[[maybe_unused]] auto {get_any_has_forward_grad_name(derivative.var_names)} = {requires_fw_grad};"
                )
        else:
            for derivative in fw_derivatives:
                bool_vector_name = get_any_has_forward_grad_name(derivative.var_names)
                cur_derivative_conditions = []
                for inp in differentiable_inputs:
                    if derivative.required_inputs_fw_grad is None:
                        continue
                    if inp.name not in derivative.required_inputs_fw_grad:
                        continue
                    inp_name = (
                        inp.name
                        if not inplace
                        else refargname2inplace_foreacharg[inp.name].name
                    )
                    inp_type = (
                        inp.type
                        if not inplace
                        else refargname2inplace_foreacharg[inp.name].type
                    )
                    is_list_type = is_tensor_list_type(inp_type)
                    if is_list_type:
                        if inp_name != "self":
                            content.append(
                                FW_DERIVATIVE_SIZE_CHECK_TEMPLATE.substitute(
                                    inp_name=inp_name
                                )
                            )
                        cur_derivative_conditions.append(
                            FW_DERIVATIVE_CHECK_TEMPLATE.substitute(
                                req_inp=inp_name + "[i]"
                            )
                        )
                    else:
                        cur_derivative_conditions.append(
                            FW_DERIVATIVE_CHECK_TEMPLATE.substitute(req_inp=inp_name)
                        )

                content.append(f"std::vector<bool> {bool_vector_name}(self.size());")
                content.append("for (const auto& i : c10::irange(self.size())) {")
                content.append(
                    f"  {bool_vector_name}[i] = {' || '.join(cur_derivative_conditions)};"
                )
                content.append("}")
        return content

    def emit_check_inplace() -> list[str]:
        if not inplace:
            return []
        return [
            f"check_inplace({arg.name}, _any_requires_grad);"
            for arg in differentiable_outputs
        ]

    def emit_fw_derivatives() -> list[str]:
        content: list[str] = []
        fw_grad_setters: list[str] = []
        for derivative in fw_derivatives:
            res = derivative.var_names
            if f.func.name.name.inplace:
                if len(res) != 1:
                    raise AssertionError(
                        f"Expected number of outputs to be 1 if function is inplace, got {len(res)}"
                    )
                # TODO update this when inplace namings are unified
                res = ("self",)

            if derivative.required_inputs_fw_grad is None:
                raise AssertionError("derivative.required_inputs_fw_grad is None")

            unpacked_arguments = ""
            for inp in differentiable_inputs:
                inp_name = inp.name
                is_input_tensorlist = is_foreach and is_tensor_list_type(
                    inp.type
                    if not inplace
                    else refargname2inplace_foreacharg[inp.name].type
                )
                input_suffix = "[i]" if is_input_tensorlist else ""
                if is_inplace_foreach:
                    if inp.name in refargname2inplace_foreacharg:
                        inp_name = refargname2inplace_foreacharg[inp.name].name
                zeros_fn = (
                    "zeros_symint"
                    if inplace and inp.name == "self"
                    else "_efficientzerotensor_symint"
                )
                if inp.name in derivative.required_inputs_fw_grad:
                    unpacked_arguments += (
                        FW_DERIVATIVE_DEFINED_GRAD_TEMPLATE.substitute(
                            inp_name=inp.name,
                            inp=inp_name + input_suffix,
                            zeros_fn=zeros_fn,
                        )
                    )
                    if zeros_fn == "_efficientzerotensor_symint":
                        unpacked_arguments += (
                            FW_DERIVATIVE_UPDATE_WRAPPED_NUM_TEMPLATE.substitute(
                                inp_name=inp.name
                            )
                        )

                if inp.name in (derivative.required_inputs_primal or []):
                    unpacked_arguments += (
                        FW_DERIVATIVE_DEFINED_PRIMAL_TEMPLATE.substitute(
                            inp_name=inp.name,
                            inp=inp_name + input_suffix,
                        )
                    )
            if derivative.required_original_self_value:
                input_suffix = "s[i]" if is_inplace_foreach else ""
                unpacked_arguments += FW_DERIVATIVE_DEFINED_GRAD_TEMPLATE.substitute(
                    inp_name="original_self",
                    inp="original_self" + input_suffix,
                    # pyrefly: ignore [unbound-name]
                    zeros_fn=zeros_fn,
                )
                unpacked_arguments += FW_DERIVATIVE_DEFINED_PRIMAL_TEMPLATE.substitute(
                    inp_name="original_self",
                    inp="original_self" + input_suffix,
                )
            elif inplace and derivative.is_reusing_outplace_formula:
                # The gradient wasn't already cloned, do it if grad mode is enabled
                unpacked_arguments += (
                    "self_t = GradMode::is_enabled() ? self_t.clone() : self_t;"
                )

            if inplace:
                is_inplace_str = "true"
            else:
                is_inplace_str = "false"

            requires_fw_grad = get_any_has_forward_grad_name(derivative.var_names)

            if all(
                (isinstance(var_type, BaseType) and var_type.is_tensor_like())
                for var_type in derivative.var_types
            ):
                # Is there a way to get from BaseType to BaseCType
                if len(derivative.var_types) == 1:
                    opt_res_grad_type = OptionalCType(BaseCType(tensorT)).cpp_type()
                    if not is_foreach:
                        fw_grad_setters.append(
                            FW_DERIVATIVE_SETTER_TENSOR.substitute(
                                out_arg=res[0], is_inplace=is_inplace_str
                            )
                        )
                    else:
                        expected_res = "result" if not inplace else "self"
                        if res[0] != expected_res:
                            raise AssertionError(
                                f"res[0] is {res[0]}, expected {expected_res}"
                            )
                        fw_grad_setters.append(
                            FW_DERIVATIVE_SETTER_TENSOR_FOREACH.substitute(
                                out_arg=res[0], is_inplace=is_inplace_str
                            )
                        )
                    requires_fw_grad += f" && ({derivative.var_names[0]}.defined())"
                else:
                    tuple_type = TupleCType(
                        [BaseCType(tensorT)] * len(derivative.var_types)
                    )
                    opt_res_grad_type = OptionalCType(tuple_type).cpp_type()
                    for idx, single_res in enumerate(res):
                        fw_grad_setters.append(
                            FW_DERIVATIVE_SETTER_MULTI_OUTPUT.substitute(
                                idx=idx, all_res="_".join(res), out_arg=single_res
                            )
                        )
            elif (
                isinstance(derivative.var_types[0], ListType)
                and derivative.var_types[0].is_tensor_like()
            ):
                if len(derivative.var_types) != 1:
                    raise AssertionError(
                        f"Expected number of outputs to be 1 if function returns ListType, got {len(derivative.var_types)}"
                    )
                if not is_foreach:
                    opt_res_grad_type = OptionalCType(
                        VectorCType(BaseCType(tensorT))
                    ).cpp_type()
                    fw_grad_setters.append(
                        FW_DERIVATIVE_SETTER_TENSOR_LIST.substitute(
                            out_arg=res[0], is_inplace=is_inplace_str
                        )
                    )
                else:
                    # TODO(crcrpar): Should this (= the foreach specific logic) be refactored somehow?
                    # Only out-place foreach functions that have entries in `tools/autograd/derivatives.yaml`
                    # can reach here.
                    opt_res_grad_type = OptionalCType(BaseCType(tensorT)).cpp_type()
                    fw_grad_setters.append(
                        FW_DERIVATIVE_SETTER_TENSOR_FOREACH.substitute(
                            out_arg=res[0], is_inplace=is_inplace_str
                        )
                    )
            else:
                raise RuntimeError("Unsupported output type for forward derivative")

            if not is_foreach:
                fw_grad_opt_definition = f"{opt_res_grad_type} {'_'.join(res)}_new_fw_grad_opt = ::std::nullopt;"
                # View ops create fw_grad that already is a view of the base's fw_grad so just use that
                content.append(
                    FW_DERIVATIVE_TEMPLATE.substitute(
                        fw_grad_opt_definition=fw_grad_opt_definition,
                        requires_fw_grad=requires_fw_grad,
                        formula=derivative.formula,
                        out_arg="_".join(res),
                        unpacked_arguments=unpacked_arguments,
                    )
                )
            else:
                # note(crcrpar): Assuming `self` is TensorList.
                fw_grad_opt_definition = (
                    f"std::vector<{opt_res_grad_type}> {'_'.join(res)}_new_fw_grad_opts"
                    "(self.size(), ::std::nullopt);"
                )
                foreach_forward_grad_formula = derivative.formula
                _foreach_arg: Argument | DifferentiableInput
                if inplace:
                    for _foreach_arg, _ref_arg in inplace_foreacharg2refarg.items():
                        # note(crcrpar): Massage only Scalar and ArrayRef<Scalar> here.
                        if not (
                            is_tensor_type(_foreach_arg.type)
                            or is_tensor_list_type(_foreach_arg.type)
                        ):
                            pattern = _foreach_arg.name
                            if isinstance(_foreach_arg.type, ListType):
                                pattern += "[i]"
                            foreach_forward_grad_formula = (
                                foreach_forward_grad_formula.replace(
                                    _ref_arg.name, pattern
                                )
                            )
                else:
                    if (
                        "result" in foreach_forward_grad_formula
                        and "result[i]" not in foreach_forward_grad_formula
                    ):
                        foreach_forward_grad_formula = (
                            foreach_forward_grad_formula.replace("result", "result[i]")
                        )

                content.append(
                    FW_DERIVATIVE_FOREACH_TEMPLATE.substitute(
                        fw_grad_opt_definition=fw_grad_opt_definition,
                        vector_of_optional_tensor=f"{'_'.join(res)}_new_fw_grad_opts",
                        any_has_forward_grad_for_current_index=" || ".join(
                            get_any_has_forward_grad_name(derivative.var_names) + "[i]"
                            for derivative in fw_derivatives
                        ),
                        formula=foreach_forward_grad_formula,
                        unpacked_arguments=unpacked_arguments,
                    )
                )

        # Set all the grads at the end to avoid: https://github.com/pytorch/pytorch/issues/67367
        content.append("\n".join(fw_grad_setters))
        return content

    def get_any_has_fw_grad_cond(derivative: ForwardDerivative | None) -> str:
        #
        # Produces a condition string (e.g, "isFwGradDefined(grad_output) || isFwGradDefined(output)")
        #
        if derivative is None:
            # (1) If a derivative is NOT provided, cond will check fw_grad of ALL differentiable inputs
            # - Used in the out_fn case when we want to forbid fw derivatives
            # - Used in the case where the fw_derivative is not defined, but we want
            #   To check if there is a decomposition registered for jvp
            to_check: list[str] = []
            for inp in list(
                mapMaybe(
                    gen_differentiable_input,
                    f.func.arguments.non_out + list(f.func.arguments.out),  # type: ignore[operator]
                )
            ):
                if is_tensor_type(inp.type):
                    to_check.append(
                        FW_DERIVATIVE_CHECK_TEMPLATE.substitute(req_inp=inp.name)
                    )
                elif is_tensor_list_type(inp.type):
                    to_check.append(
                        FW_DERIVATIVE_TENSORLIST_CHECK_TEMPLATE.substitute(
                            req_inp=inp.name
                        )
                    )
                else:
                    raise RuntimeError(
                        f'Unsupported input type for "{name}" when forbidding forward AD usage.'
                    )
            return f"({' || '.join(to_check)})"
        else:
            # (2) If derivative is provided, use that information to determine which inputs
            #     to check fw_grad for
            if derivative.required_inputs_fw_grad is None:
                raise AssertionError("derivative.required_inputs_fw_grad is None")

            if len(derivative.required_inputs_fw_grad) == 0:
                # Handle functions like stack
                # For these, we don't unpack anything and always call the user function
                if not (
                    len(differentiable_inputs) == 1
                    and is_tensor_list_type(differentiable_inputs[0].type)
                ):
                    raise RuntimeError(
                        f'No differentiable input to "{name}" is a differentiable Tensor (as the provided '
                        "forward AD formula does not use any input tangent) even though a forward gradient "
                        "formula has been defined for it. This case should only happen for function that "
                        "take a single TensorList as input. All other cases are not supported right now."
                    )
                any_has_fw_grad = "true"
            else:
                any_has_fw_grad = " || ".join(
                    [
                        (
                            FW_DERIVATIVE_TENSORLIST_CHECK_TEMPLATE
                            if is_tensor_list_type(inp.type)
                            else FW_DERIVATIVE_CHECK_TEMPLATE
                        ).substitute(req_inp=inp.name)
                        for inp in differentiable_inputs
                        if inp.name in derivative.required_inputs_fw_grad
                    ]
                )
                any_has_fw_grad = f"({any_has_fw_grad})"

            return any_has_fw_grad

    def emit_forbid_fw_derivatives(is_out_fn: bool = False) -> str:
        if is_out_fn:
            msg = "because it is an out= function"
        else:
            msg = (
                "because it has not been implemented yet.\\nPlease file an issue "
                "to PyTorch at https://github.com/pytorch/pytorch/issues/new?template=feature-request.yml "
                "so that we can prioritize its implementation."
            )
        cond = get_any_has_fw_grad_cond(derivative=None)
        return (
            FW_DERIVATIVE_FORBID_TEMPLATE.substitute(cond=cond, name=name, msg=msg)
            if cond != ""
            else ""
        )

    body: list[str] = []
    unpack_args_stats, unpacked_bindings = unpack_args(f)

    body.extend(unpack_args_stats)
    if requires_derivative:
        body.extend(emit_any_requires_grad())
        body.extend(emit_any_has_forward_grad())
        body.extend(emit_check_inplace())
        body.extend(emit_original_self_definition())
        body.extend(setup_derivative(differentiable_inputs))

    body.append(emit_call(f, unpacked_bindings, try_jit_decomposition))
    if requires_derivative:
        # set_flags has to appear after version_counter, because rebase_history
        # requires that the counter is incremented before it is called
        body.append(emit_history())
        body.extend(emit_check_if_in_complex_autograd_allowlist())

    if is_out_fn:
        body.append(emit_forbid_fw_derivatives(is_out_fn=True))
    else:
        if requires_derivative and not try_jit_decomposition:
            if len(fw_derivatives) > 0:
                body.extend(emit_fw_derivatives())
            else:
                body.append(emit_forbid_fw_derivatives())

    if requires_derivative:
        # Save only after the forward AD has been set up
        body.append(emit_save_outputs())

    if str(f.func.name.name) in RESET_GRAD_ACCUMULATOR:
        # `inplace` implies that there is exactly one output named `self`,
        # so we can keep the generated code easy. If you need to
        # `reset_grad_accumulator` in an operator that's not `inplace`, you can
        # remove this check but the code generation will get more elaborate
        if not inplace:
            raise AssertionError(
                f"expected inplace=True for {f.func.name.name} which is in RESET_GRAD_ACCUMULATOR"
            )
        body.append("reset_grad_accumulator(self);")
    if not returns_void:
        body.append(f"return {get_return_value(f)};")
    return body
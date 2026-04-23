def match_differentiability_info(
    native_functions: list[NativeFunction],
    differentiability_infos: dict[FunctionSchema, dict[str, DifferentiabilityInfo]],
) -> list[NativeFunctionWithDifferentiabilityInfo]:
    """Sets the "derivative" key on declarations to matching autograd function
    In-place functions will use the out-of-place derivative definition if there
    is no in-place specific derivative.
    """

    functional_info_by_signature = {
        schema.signature(strip_default=True): info_dict
        for schema, info_dict in differentiability_infos.items()
        if schema.kind() == SchemaKind.functional
    }
    non_functional_info_by_signature = {
        schema.signature(strip_default=True): info_dict
        for schema, info_dict in differentiability_infos.items()
        if schema.kind() != SchemaKind.functional
    }

    def find_info(
        f: NativeFunction,
    ) -> tuple[dict[str, DifferentiabilityInfo] | None, bool]:
        # Don't bother matching info to generated out= variants
        if "generated" in f.tags and f.func.kind() == SchemaKind.out:
            return None, False

        # (1) Check for an exact match
        if f.func in differentiability_infos:
            return differentiability_infos[f.func], True

        # (2) If no exact match, check if the out-of-place variant
        # of this operator has a match.
        # i.e mul() for mul_() or mul_out()
        # note(crcrpar): Check foreach or not because in-place foreach functions use backward defined for the existing
        # native functions instead of the out-place counterparts.
        f_sig = f.func.signature(strip_default=True)
        if f_sig in functional_info_by_signature and not is_foreach_func(f):
            return functional_info_by_signature[f_sig], False

        # (3) Some operators have a derivative explicitly defined for the mutable
        # variant, but get a code-generated out-of-place variant which does *not*
        # come with a derivative formula.
        # For the generated out-of-place variant, use the mutable variant's formula
        # if it exists.
        if "generated" in f.tags and f_sig in non_functional_info_by_signature:
            info_dict = non_functional_info_by_signature[f_sig]
            # See https://github.com/pytorch/pytorch/pull/76320/files#r874816389
            if any(
                any("self" in str(input.nctype.name) for input in info.all_saved_inputs)
                for info in info_dict.values()
            ):
                raise AssertionError(
                    f"Attempted to convert a derivative formula for a mutable operator "
                    f'to be used automatically by its functional variant ("{str(f.func)}"). '
                    "This is not currently supported (we'd need to fix up the formula in the codegen)."
                )
            return info_dict, False

        # (4) Generate derivative information of foreach functions if none is defined in `derivatives.yaml`
        if is_foreach_func(f):
            if f.func in differentiability_infos:
                raise AssertionError(
                    f"Foreach function {f.func.name} already has differentiability info"
                )
            diff_info, is_generated = gen_foreach_derivativeinfo(
                f,
                functional_info_by_signature,
                non_functional_info_by_signature,
            )
            if diff_info is None:
                return None, False
            # TODO(crcrpar): Avoid hard coding "Default" ideally.
            diff_info_dict = {"Default": diff_info}
            if is_generated:
                differentiability_infos[f.func] = diff_info_dict
                functional_info_by_signature[f.func] = diff_info_dict
            return diff_info_dict, is_generated

        return None, False

    result: list[NativeFunctionWithDifferentiabilityInfo] = []
    for f in native_functions:
        info_dict, is_exact_match = find_info(f)

        # Currently, the '.strides()' to 'strides_or_error' replacement does not support
        # 'self' derivatives of an inplace function, so we must check for this case.
        if f.func.kind() == SchemaKind.inplace and (info_dict is not None):
            for info in info_dict.values():
                for derivative in info.derivatives:
                    if "self" in derivative.var_names:
                        for saved_input in derivative.saved_inputs:
                            if "strides_or_error" in saved_input.expr:
                                raise AssertionError(
                                    "Calling '.strides()' in the 'self' derivative formula of an "
                                    f"in-place function is not supported: {f.func}"
                                )

        if not info_dict:
            result.append(
                NativeFunctionWithDifferentiabilityInfo(
                    func=f, info=None, fw_derivatives=None
                )
            )
            continue

        fw_derivative_dict: dict[str, Sequence[ForwardDerivative]] = {}
        for key, info in info_dict.items():
            if not info.forward_derivatives:
                fw_derivative_dict[key] = []
                continue

            forward_derivatives = info.forward_derivatives

            # For functions that have a single def for out-of-place and inplace (like abs())
            if f.func.kind() == SchemaKind.inplace:
                # For inplace functions there is a little bit of work to do:
                #  1) Validate the formula and make sure the input that is modified in not used:
                #    - If there is a formula for the inplace variant of the function (is_exact_match == True) then
                #      we make sure that the original value of the input that is being modified inplace (self_p) is
                #      not used in the formula. Note that the formula can use "original_self_p" here and that would
                #      trigger a clone of the original input.
                #    - If we are reusing the out of place formula (is_exact_match == False) then we replace every
                #      occurrence of self_p and self_t by original_self_p and original_self_t. These will be
                #      populated by cloned version of the original input (either the clone done by the backward AD
                #      logic if self is also used in a backward formula or a special clone that we add).
                #  2) At this point, there cannot be a self_p in the formula.
                #  3) Change "result" into "self_p" as by design, in the inplace function codegen, the result is
                #     simply called self (as it is modified inplace).
                #  4) Update the required primals data in case it used to contain "result" but should now contain
                #     "self"
                #  5) If it is not an exact match, the user formula is not modifying the existing forward grad
                #     inplace as it should. So add some code that makes sure that we do so if the forward grad
                #     already exists.

                if len(info.forward_derivatives) != 1:
                    raise AssertionError(
                        "Only single output inplace should exist, "
                        f"got {len(info.forward_derivatives)}"
                    )
                fw_info = info.forward_derivatives[0]
                formula = fw_info.formula

                def replace_self_with_original_self(formula: str, postfix: str) -> str:
                    def repl(m: re.Match[str]) -> str:
                        return f"{m.group(1)}original_self{postfix}{m.group(2)}"

                    return re.sub(IDENT_REGEX.format(f"self{postfix}"), repl, formula)

                if re.search(IDENT_REGEX.format("self_p"), formula):
                    if is_exact_match:
                        # For manually defined formulas, don't allow the original value to be used
                        raise RuntimeError(
                            f'The formula for "{f.func.name}" is using the original value of self '
                            "that is being modified inplace. This would lead to wrong forward gradients. "
                            'Please use "result" in the formula only.'
                        )
                    else:
                        # When the original formula is out of place, we save a clone of the primal
                        # value to be able to access this value if needed
                        # replace "self_p"/"self_t" from the formula by "original_self_p"/"original_self_t"
                        formula = replace_self_with_original_self(formula, "_p")
                        formula = replace_self_with_original_self(formula, "_t")

                # replace "result" from the formula by "self_p"
                def repl(m: re.Match[str]) -> str:
                    return f"{m.group(1)}self_p{m.group(2)}"

                formula = re.sub(IDENT_REGEX.format("result"), repl, formula)

                required_primals = fw_info.required_inputs_primal
                if re.search(IDENT_REGEX.format("self_p"), formula):
                    required_primals = (
                        required_primals + ("self",) if required_primals else ("self",)
                    )

                if not is_exact_match:
                    # NOTE [In-place forward AD formula Optimization]
                    #
                    # This optimization transforms the formula to directly do inplace, i.e.
                    # instead of self_t.copy_(self_t.op()) we do self_t.op_() when the following are met:
                    #
                    # 1) the formula satisfies the pattern: "self_t.op(*args)"
                    # 2) "op" in (1) needs to be the same as the op the derivative is for
                    #
                    # (2) may seem too strict, but currently the only ops that satisfy (1) also satisfy (2)
                    # If there is a need, we can relax (2) to allow any op that has an in-place variant
                    is_single_method_on_self_t = False
                    directly_do_inplace = False
                    op_name: str | None = None
                    between_parens: str | None = None
                    match = re.fullmatch(r"self_t.([\w]*)\((.*)\)", formula)
                    if match:
                        op_name, between_parens = match.group(1), match.group(2)

                        # We want to...
                        #   Match: self_t.op1(other_p.op2(arg))
                        #   Avoid: self_t.op1(args) + self_t.op2(args)
                        #   Avoid: self_t.op1(other_p.op2(arg)) + self_t.op2(args)
                        def check_parens_nest_level_gt_zero(s: str) -> bool:
                            level = 1
                            for ch in s:
                                if ch == ")":
                                    level -= 1
                                    if level == 0:
                                        return False
                                if ch == "(":
                                    level += 1
                            return True

                        is_single_method_on_self_t = check_parens_nest_level_gt_zero(
                            between_parens
                        )
                        directly_do_inplace = (
                            is_single_method_on_self_t and op_name == info.name
                        )

                    if directly_do_inplace:
                        if op_name is None:
                            raise AssertionError("op_name must be non-None for inplace")
                        if between_parens is None:
                            raise AssertionError(
                                "between_parens must be non-None for inplace"
                            )
                        formula = f"self_t_raw.defined() ? self_t_raw.{op_name}_({between_parens}) : {formula}"
                    else:
                        # Make sure that the forward grad is modified inplace when the original formula
                        # is out of place
                        formula = f"self_t_raw.defined() ? self_t_raw.copy_({formula}) : {formula}"

                required_original_self_value = bool(
                    re.search(IDENT_REGEX.format("original_self_p"), formula)
                ) or bool(re.search(IDENT_REGEX.format("original_self_t"), formula))

                forward_derivatives = [
                    ForwardDerivative(
                        formula=formula,
                        var_names=("self",),
                        var_types=fw_info.var_types,
                        required_inputs_fw_grad=fw_info.required_inputs_fw_grad,
                        required_inputs_primal=required_primals,
                        required_original_self_value=required_original_self_value,
                        is_reusing_outplace_formula=not is_exact_match,
                    ),
                ]

            fw_derivative_dict[key] = forward_derivatives

        result.append(
            NativeFunctionWithDifferentiabilityInfo(
                func=f, info=info_dict, fw_derivatives=fw_derivative_dict
            )
        )

    return result
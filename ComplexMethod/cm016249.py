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
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
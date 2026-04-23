def postprocess_forward_derivatives(
    f: NativeFunction,
    defn_name: str,
    all_arg_names: list[str],
    derivatives: list[Derivative],
    forward_derivatives: list[ForwardDerivative],
    args_with_derivatives: Sequence[Binding],
) -> list[ForwardDerivative]:
    def find_required_inputs(formula: str, postfix: str) -> tuple[str, ...]:
        is_foreach = f.func.name.name.base.startswith("_foreach_")
        required_inputs = set()
        for arg in args_with_derivatives:
            if (
                arg.type in ("at::TensorList", "const at::ITensorListRef &")
                and not is_foreach
            ):
                # The functions taking TensorList handle everything internally
                continue
            arg_name = arg.name

            found = re.search(IDENT_REGEX.format(arg_name), formula)
            if found:
                raise RuntimeError(
                    f"The forward formula for {defn_name} is using the base name of the {arg_name} "
                    f"argument which is ambiguous. You should use {arg_name}_p to access the primal "
                    f"value and {arg_name}_t to access the tangent."
                )

            found = re.search(IDENT_REGEX.format(arg_name + postfix), formula)
            if found:
                required_inputs.add(arg_name)

        return tuple(required_inputs)

    updated_derivatives: list[ForwardDerivative] = []

    for defn in forward_derivatives:
        formula = defn.formula
        required_inputs_tangent = find_required_inputs(formula, "_t")
        if formula == "auto_element_wise":
            if f.func.kind() == SchemaKind.inplace:
                raise AssertionError(
                    f"Cannot use auto_element_wise with {f.func.name} because it is an in-place variant"
                )
            if (
                (not len(args_with_derivatives) == 1)
                or len(forward_derivatives) > 1
                or len(forward_derivatives[0].var_names) > 1
            ):
                raise RuntimeError(
                    f"Derivative definition of {defn_name} in derivatives.yaml defines the "
                    "forward definition of gradient as element_wise but this only "
                    "works for functions with a single differentiable input and a "
                    "single differentiable output."
                )
            if not len(derivatives) == 1:
                raise RuntimeError(
                    f"Derivative definition of {defn_name} in derivatives.yaml defines the "
                    "forward definition of gradient as element_wise but it does not "
                    "defines the gradient formula for its argument which is required."
                )
            # This transformation is based on the observation that for element-wise functions, the Jacobian
            # matrix is diagonal and thus doing J * v is the same as (v^T J)^T (in practice, we ignore the transpositions)
            # For the complex case, we use hermitian transpose and get (v.conj() J).conj()
            # So here we are going to reuse the backward formula and replace two things:
            # 1) all occurrences of "grad" with "foo_t.conj()", where foo is the name of the unique differentiable input.
            # 2) all usage of an original input "foo" with its primal value "foo_p".
            # 3) conjugate the final result
            # For example, for abs, the backward formula is:
            #   grad * self.sgn()
            # And this function generates a forward formula that is:
            #   (self_t.conj() * self_p.sgn()).conj()

            backward_formula = derivatives[0].original_formula
            input_name = args_with_derivatives[0].name

            # Do replacement 1) of the grad
            def repl(m: Any) -> str:
                return f"{m.group(1)}{input_name}_t.conj(){m.group(2)}"

            fw_formula = re.sub(IDENT_REGEX.format("grad"), repl, backward_formula)

            # Do replacement 2) of the input variables
            for arg in args_with_derivatives:
                arg_name = arg.name

                def repl(m: Any) -> str:
                    return f"{m.group(1)}{arg_name}_p{m.group(2)}"

                fw_formula = re.sub(IDENT_REGEX.format(arg_name), repl, fw_formula)

            # Do the final conjugate 3)
            fw_formula = f"({fw_formula}).conj()"

            # Since there is a single differentiable inputs and we necessarily need its tangent we can
            # simply require all differentiable input's tangent.
            required_inputs_tangent = tuple(all_arg_names)
            formula = fw_formula
        elif formula == "auto_linear":
            if (
                len(forward_derivatives) > 1
                or len(forward_derivatives[0].var_names) > 1
            ):
                raise RuntimeError(
                    f"Derivative definition of {defn_name} in derivatives.yaml defines the "
                    "forward definition of gradient as linear but this only works "
                    "for functions with a single differentiable output."
                )
            # This transformation is based on the observation that linear functions can be written as:
            #   y = f(x) = A * x
            # For some matrix A and the Jacobian of the function f is also A.
            # So doing J * v = A * v = f(v).
            # Hence to do the jvp, we simply need to evaluate the function at the point v instead of x.
            # We do this by calling the forward again by replacing any occurrence of the differentiable
            # input "foo" by it's tangent "foo_t".
            # Note that multiple inputs are not a problem as long as the function is truly linear wrt to
            # the vector where all the differentiable inputs are stacked.

            diff_arg_names = [arg.name for arg in args_with_derivatives]
            if len(diff_arg_names) == 0:
                raise AssertionError("Expected at least one differentiable argument")

            # Do replacement of input variables
            new_args = []
            for arg_name in all_arg_names:
                if arg_name in diff_arg_names:
                    arg_name = arg_name + "_t"
                new_args.append(arg_name)

            # TODO we are trolling
            if f.func.has_symint():
                defn_name += "_symint"

            # Call into the forward again. We need two cases here to handle both Tensor methods and at:: functions.
            if Variant.function in f.variants:
                fw_formula = f"at::{defn_name}({', '.join(new_args)})"
            else:
                if Variant.method not in f.variants:
                    raise AssertionError(
                        f"Expected Variant.method in variants for {f.func.name}"
                    )
                fw_formula = f"{new_args[0]}.{defn_name}({', '.join(new_args[1:])})"

            # All of the input tangents are always used so all of them are required here.
            required_inputs_tangent = tuple(diff_arg_names)
            formula = fw_formula

        # At this point, the formula is final and is not modified anymore.

        # During forward formula, we use the primal instead of the input Tensors.
        # This call inspects the formula to find for which input's primal are used.
        required_inputs_primal = find_required_inputs(formula, "_p")

        updated_derivatives.append(
            ForwardDerivative(
                formula=formula,
                var_names=defn.var_names,
                var_types=defn.var_types,
                required_inputs_fw_grad=required_inputs_tangent,
                required_inputs_primal=required_inputs_primal,
                required_original_self_value=False,
                is_reusing_outplace_formula=False,
            )
        )

    return updated_derivatives
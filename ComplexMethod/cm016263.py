def set_up_derivatives(
        f: NativeFunction,
    ) -> tuple[
        Sequence[Derivative],
        Sequence[ForwardDerivative],
        Sequence[Binding],
        Sequence[str],
        Sequence[str],
    ]:
        # Set up the derivative information
        derivatives: list[Derivative] = []
        forward_derivatives: list[ForwardDerivative] = []
        non_differentiable_arg_names: list[str] = []
        args_with_derivatives_set: set[str] = set()

        all_arg_names = [a.name for a in cpp_arguments(f)]
        all_ret_names = [
            r.name for r in f.func.returns
        ]  # only used for the assert below
        # output_differentiability is captured from the enclosed
        # scope. Don't modify it.
        #
        # If it is not present, then no output is explicitly
        # undifferentiable.
        #
        # It may be present and shorter than the length of return
        # values. If that's the case, any return value that does not
        # have a corresponding entry is considered not differentiable.
        differentiability = output_differentiability or [True] * len(f.func.returns)
        # A return is available as a named gradient ...
        available_named_gradients = [
            f"grad_{ret.name}"
            for ret, differentiable in zip(f.func.returns, differentiability)
            # if it has not been explicitly made undifferentiable
            if differentiable
            # and if it has a name
            and ret.name is not None
            # and if its type is differentiable
            and ret.type.is_tensor_like()
        ]

        for raw_names in sorted(defn.keys()):
            formula = defn[raw_names]
            names = split_names(raw_names)

            for name in names:
                if name in all_arg_names and name in all_ret_names:
                    raise AssertionError(
                        f"While processing the derivative formula for '{f.func.name}' wrt '{name}', "
                        f"expected '{name}' to not be both an input arg and named return."
                    )

            if is_forward_derivative_definition(all_arg_names, names):
                forward_derivatives.append(create_forward_derivative(f, formula, names))
            else:
                if formula.lower().strip() == "non_differentiable":
                    non_differentiable_arg_names += names
                else:
                    derivative = create_derivative(
                        f, formula, names, available_named_gradients
                    )
                    derivatives.append(derivative)
                    args_with_derivatives_set |= set(names)

        overlap = args_with_derivatives_set.intersection(non_differentiable_arg_names)
        if overlap:
            raise RuntimeError(
                f"derivatives definition for {defn} have overlapped non_differentiable "
                f"and differentiable variables: {overlap}"
            )

        # Next, let us determine the list of inputs in order.
        # TODO: do we need eagerly calculate and save it here? Can it be derived
        # from NativeFunction and `derivatives` on callsites instead?
        args_with_derivatives = [
            a for a in cpp_arguments(f) if a.name in args_with_derivatives_set
        ]

        # Postprocess forward derivatives definitions now that we know the differentiable arguments
        forward_derivatives = postprocess_forward_derivatives(
            f,
            defn_name,
            all_arg_names,
            derivatives,
            forward_derivatives,
            args_with_derivatives,
        )

        # Test to see if the use of 'grads' makes sense.
        check_grad_usage(defn_name, derivatives)

        return (
            derivatives,
            forward_derivatives,
            args_with_derivatives,
            non_differentiable_arg_names,
            available_named_gradients,
        )
def check_grad_usage(defn_name: str, derivatives: Sequence[Derivative]) -> None:
        """
        Check for some subtle mistakes one might make when writing derivatives.
        These mistakes will compile, but will be latent until a function is
        used with double backwards.
        """

        uses_grad = False  # true if any derivative uses "grad"
        num_grads_uses = 0  # count of uses of "grads" or "grads[INDEX]"
        uses_named_grads = False  # true if any derivative uses "grad_{name}"
        used_grads_indices: list[int] = []  # which indices of grads are used
        for d in derivatives:
            formula = d.formula
            uses_grad = uses_grad or bool(
                re.findall(IDENT_REGEX.format("grad"), formula)
            )
            num_grads_uses += len(re.findall(IDENT_REGEX.format("grads"), formula))
            uses_named_grads = uses_named_grads or bool(d.named_gradients)
            used_grads_indices.extend(used_gradient_indices(formula))
        # This is a basic sanity check: the number of places we see
        # "grads" should be no fewer than the number of indices we see
        # inside "grads". They may not be equal because we may use
        # "grads" without an index.
        if num_grads_uses < len(used_grads_indices):
            raise AssertionError(
                f"num_grads_uses ({num_grads_uses}) < len(used_grads_indices) ({len(used_grads_indices)})"
            )
        # Thus if the number is equal, every use of grads is also
        # indexed.
        only_used_grads_indices = num_grads_uses == len(used_grads_indices)

        if uses_grad and num_grads_uses > 0:
            raise RuntimeError(
                f"Derivative definition of {defn_name} in derivatives.yaml illegally "
                "mixes use of 'grad' and 'grads'. Consider replacing "
                "occurrences of 'grad' with 'grads[0]'"
            )

        if only_used_grads_indices and set(used_grads_indices) == {0}:
            raise RuntimeError(
                f"Derivative definition of {defn_name} in derivatives.yaml solely "
                "refers to 'grads[0]'.  If the first output is indeed the "
                "only differentiable output, replace 'grads[0]' with 'grad'; "
                "otherwise, there is a likely error in your derivatives "
                "declaration."
            )

        if uses_named_grads and (uses_grad or num_grads_uses > 0):
            raise RuntimeError(
                f"Derivative definition of {defn_name} in derivatives.yaml illegally "
                'mixes use of "grad_RETURN_NAME" and "grad" or "grads[x]". Use '
                "only one method for identifying gradients."
            )
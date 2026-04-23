def compute_output_spec(self, *operands):
        """Compute the output shape of `einsum`.

        The shape computation follows the steps below:
        1. Find all letters in the input specs (left part of "->"), and
            break them into two categories: letters appearing more than once
            go to `reduced_dims`, otherwise go to `kept_dims`.
        2. Adjust `reduced_dims` and `kept_dims` based on the output spec
            (right part of "->"). The rule is if the letter appears in the
            output spec, then move it to `kept_dims`, otherwise move it to
            `reduced_dims`.
        3. Compute the target output shape. If no output spec is set, then
            the target output shape will be "...{kept_dims}", e.g., "...ijk",
            else it will be the same as output spec. "..." is a wildcard that
            could map shape of arbitrary length.
        4. For each operand in `operands`, map the shape specified in the input
            spec to the output target, e.g, if operand is of shape [2,3,4],
            input spec is "i..." and output target is "i...jk", then 2 will go
            the index 0. For dims not represented by any letter, insert to the
            wildcard part. For each letter in output target not appearing in
            input spec, the dim will be 1 for broadcasting. After 4, each
            operand should have a target shape containing only number and
            `None`.
        5. Broadcast all shapes computed from 4, and the result is the output
            shape.

        Let's take an example to illustrate the steps above. Let's define:
        ```python
        x = KerasTensor([None, 3, 4])
        y = KerasTensor(2, 4, 3)
        z = knp.einsum("...ij, kji->...k", x, y)
        ```

        1. `reduced_dims` is {"i", "j"}, `kept_dims` is {"k"}.
        2. `reduced_dims` is still {"i", "j"}, and `kept_dims` is {"k"}.
        3. Output target is "...k".
        4. For `x`, the input spec is "...ij", and the output target is "...k".
            "i" and "j" do not appear in the output target, so no replacement
            happens, and [None] goes to wildcard. Afterwards, "k" is replaced
            by 1, so we get shape [None, 1]. Applying the same logic to `y`, we
            get shape [2].
        5. Broadcast [None, 1] and [2], and we get [None, 2], which is the
            output shape.
        """
        split_subscripts = self.subscripts.split("->")
        if len(split_subscripts) > 2:
            raise ValueError(
                "At most one '->' is supported in `einsum` subscripts, but "
                f"received {self.subscripts}."
            )
        if len(split_subscripts) == 2:
            subscripts = split_subscripts[0]
            output_spec = split_subscripts[1]
        else:
            subscripts = self.subscripts
            output_spec = None
        input_specs = subscripts.split(",")
        if len(input_specs) != len(operands):
            raise ValueError(
                f"Number of operands ({len(operands)}) does not match the "
                f"number of input specs ({len(input_specs)}) in `einsum`, "
                f"received subscripts={self.subscripts}."
            )
        reduced_dims = set()
        kept_dims = set()
        for s in subscripts:
            if not s.isalpha():
                continue
            if s not in reduced_dims and s not in kept_dims:
                kept_dims.add(s)
            elif s in kept_dims:
                kept_dims.remove(s)
                reduced_dims.add(s)

        if output_spec is not None:
            # The output spec changes the rule of kept_dims and reduced_dims.
            # In short, dims appearing in the output spec will be kept, and
            # dims not appearing in the output spec will be reduced.
            kept_dims_copy = kept_dims.copy()
            reduced_dims_copy = reduced_dims.copy()
            for dim in kept_dims:
                if dim not in output_spec:
                    kept_dims_copy.remove(dim)
                    reduced_dims_copy.add(dim)
            for dim in reduced_dims:
                if dim in output_spec:
                    reduced_dims_copy.remove(dim)
                    kept_dims_copy.add(dim)
            kept_dims = kept_dims_copy
            reduced_dims = reduced_dims_copy

        reduced_dims = sorted(reduced_dims)
        kept_dims = sorted(kept_dims)

        if output_spec is None:
            target_broadcast_spec = f"...{''.join(kept_dims)}"
        else:
            target_broadcast_spec = output_spec

        expanded_operands_shapes = []
        for x, spec in zip(operands, input_specs):
            x_shape = getattr(x, "shape", [])
            x_shape = [-1 if size is None else size for size in x_shape]
            split_spec = spec.split("...")
            expanded_shape = target_broadcast_spec
            if len(split_spec) == 1:
                # In this case, the input spec is just a string of letters,
                # e.g., "ijk".
                if len(x_shape) != len(split_spec[0]):
                    raise ValueError(
                        "Number of dimensions in the subscript does not "
                        "match the number of dimensions in the operand, "
                        f"received subscript `{spec}` and operand of shape "
                        f"{x_shape}."
                    )
                for size, s in zip(x_shape, split_spec[0]):
                    # Replace the letter with the right shape.
                    expanded_shape = expanded_shape.replace(s, f"{str(size)} ")
                expanded_shape = expanded_shape.replace("...", "")
            else:
                # In this case, the input spec has "...", e.g., "i...j", "i...",
                # or "...j".
                for i in range(len(split_spec[0])):
                    expanded_shape = expanded_shape.replace(
                        split_spec[0][i], f"{x_shape[i]} "
                    )
                for i in range(len(split_spec[1])):
                    expanded_shape = expanded_shape.replace(
                        split_spec[1][-i - 1], f"{x_shape[-i - 1]} "
                    )
                # Shape matched by "..." will be inserted to the position of
                # "...".
                wildcard_shape_start_index = len(split_spec[0])
                wildcard_shape_end_index = (
                    len(x_shape)
                    if len(split_spec[1]) == 0
                    else -len(split_spec[1])
                )
                wildcard_shape = x_shape[
                    wildcard_shape_start_index:wildcard_shape_end_index
                ]
                wildcard_shape_str = (
                    f"{' '.join([str(size) for size in wildcard_shape])} "
                )
                expanded_shape = expanded_shape.replace(
                    "...", wildcard_shape_str
                )
            # Replace all letters not yet handled with "1" for broadcasting.
            expanded_shape = re.sub("[a-z]", "1 ", expanded_shape)
            expanded_shape = expanded_shape.split()
            expanded_shape = [
                None if size == "-1" else int(size) for size in expanded_shape
            ]
            expanded_operands_shapes.append(expanded_shape)

        output_shape = expanded_operands_shapes[0]
        for shape in expanded_operands_shapes[1:]:
            output_shape = broadcast_shapes(output_shape, shape)
        dtypes_to_resolve = list(
            set(
                backend.standardize_dtype(getattr(x, "dtype", type(x)))
                for x in operands
            )
        )
        if len(dtypes_to_resolve) == 1 and dtypes_to_resolve[0] == "int8":
            dtype = "int32"
        else:
            dtype = dtypes.result_type(*dtypes_to_resolve)
        return KerasTensor(output_shape, dtype=dtype)
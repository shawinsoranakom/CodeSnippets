def inner(*inputs: list[list[TensorBox]], alpha=1, value=1):
        # For ops like addcmul/addcdiv, the scalar `value` arrives as a
        # positional arg (not keyword) due to the ATen schema. Extract it
        # from the end of inputs if present.
        # pyrefly: ignore [bad-assignment]
        inputs = list(inputs)
        if (
            scalar_kwarg == "value"
            and inputs
            and not isinstance(inputs[-1], (list, tuple))
        ):
            # pyrefly: ignore [missing-attribute]
            scalar_val = inputs.pop()
        elif scalar_kwarg == "value":
            scalar_val = value
        else:
            scalar_val = alpha

        realize_outputs = (
            len(V.graph.current_node.users) == 0
            or V.graph.current_node.target in inplace_foreach_ops
            or cur_node_has_non_foreach_users()
        )

        a_list_input = None
        for input in inputs:
            if isinstance(input, (list, tuple)):
                a_list_input = input
                break
        assert a_list_input is not None, (
            "at least one input must be a list to a foreach op"
        )

        # broadcast scalar inputs to match length of list inputs
        broadcast_inputs = []
        for input in inputs:
            if not isinstance(input, (list, tuple)):
                broadcast_inputs.append([input] * len(a_list_input))
            else:
                # pyrefly: ignore [bad-argument-type]
                broadcast_inputs.append(input)

        groups = group_foreach_args(zip(*broadcast_inputs))

        def apply_fn(args):
            if allow_alpha:
                return pw_fn(*args, **{scalar_kwarg: scalar_val})
            else:
                return pw_fn(*args)

        return foreach_group_loop(groups, len(a_list_input), apply_fn, realize_outputs)
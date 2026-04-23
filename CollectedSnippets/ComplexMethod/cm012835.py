def validate_grad_inputs_dict(grad_inputs_dict, forward_op, args_info):
    def error(what):
        backward = forward_op._get_impl("backward")
        raise RuntimeError(
            f"In the backward function defined for {forward_op} at "
            f"{backward.location} using the CustomOp API, {what}"
        )

    if not isinstance(grad_inputs_dict, dict):
        error(
            f"expected the output of the backward function to be a dict but "
            f"got {type(grad_inputs_dict)}"
        )

    expected_keys = {
        arg.name
        for arg in forward_op._schema.arguments.flat_all
        if arg.type.is_tensor_like()
    }
    actual_keys = grad_inputs_dict.keys()
    if expected_keys != actual_keys:
        error(
            f"expected the returned grad_input dict to have keys "
            f"{expected_keys} but got {actual_keys}. The backward "
            f"function must return a gradient (can be None) for each arg "
            f"to the CustomOp that may be a Tensor or Sequence[Tensor]. "
            f"Args declared to be non-Tensor-like types should not appear "
            f"in the grad_input dict"
        )

    for name, grad in grad_inputs_dict.items():
        arg_info = getattr(args_info, name)

        if isinstance(arg_info, list):
            if not isinstance(grad, (tuple, list)):
                error(
                    f"for input '{name}' expected the grad_input dict to "
                    f"hold a list of gradients but got object of type "
                    f"{type(grad)}."
                )
            if len(grad) != len(arg_info):
                error(
                    f"for input '{name}' expected the grad_input dict to "
                    f"hold a list of {len(arg_info)} gradients but got "
                    f"{len(grad)}"
                )
            for idx, (g, info) in enumerate(zip(grad, arg_info)):
                if g is None:
                    continue
                if not isinstance(g, torch.Tensor):
                    error(
                        f"for input '{name}' expected the grad_input dict to "
                        f"hold a list of None or Tensor gradients but got "
                        f"object of {type(g)} at index {idx}"
                    )
                if not issubclass(info, torch.Tensor):
                    error(
                        f"for input '{name}', got a Tensor as the gradient "
                        f"for the {idx}-th value but expected None because "
                        f"the {idx}-th value was not a Tensor (it was "
                        f"type {arg_info}"
                    )
            continue

        if grad is None:
            continue
        if not isinstance(grad, torch.Tensor):
            error(
                f"got object of type {type(grad)} as the gradient for input "
                f"'{name}', "
                f"but expected the gradient to be either None or a Tensor"
            )
        if not issubclass(arg_info, torch.Tensor):
            error(
                f"got a Tensor as the gradient for input '{name}' but "
                f"expected None as the gradient because input '{name}' "
                f"was not a Tensor (it was type {arg_info})."
            )
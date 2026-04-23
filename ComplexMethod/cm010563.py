def _fill_in_zeros(grads, refs, strict, create_graph, stage):
    # Used to detect None in the grads and depending on the flags, either replace them
    # with Tensors full of 0s of the appropriate size based on the refs or raise an error.
    # strict and create graph allow us to detect when it is appropriate to raise an error
    # stage gives us information of which backward call we consider to give good error message
    if stage not in ["back", "back_trick", "double_back", "double_back_trick"]:
        raise RuntimeError(f"Invalid stage argument '{stage}' to _fill_in_zeros")

    res: tuple[torch.Tensor, ...] = ()
    for i, grads_i in enumerate(grads):
        if grads_i is None:
            if strict:
                if stage == "back":
                    raise RuntimeError(
                        "The output of the user-provided function is independent of "
                        f"input {i}. This is not allowed in strict mode."
                    )
                elif stage == "back_trick":
                    raise RuntimeError(
                        f"The gradient with respect to the input is independent of entry {i}"
                        " in the grad_outputs when using the double backward trick to compute"
                        " forward mode gradients. This is not allowed in strict mode."
                    )
                elif stage == "double_back":
                    raise RuntimeError(
                        "The jacobian of the user-provided function is independent of "
                        f"input {i}. This is not allowed in strict mode."
                    )
                else:
                    raise RuntimeError(
                        "The hessian of the user-provided function is independent of "
                        f"entry {i} in the grad_jacobian. This is not allowed in strict "
                        "mode as it prevents from using the double backward trick to "
                        "replace forward mode AD."
                    )

            grads_i = torch.zeros_like(refs[i])
        else:
            if strict and create_graph and not grads_i.requires_grad:
                if "double" not in stage:
                    raise RuntimeError(
                        "The jacobian of the user-provided function is independent of "
                        f"input {i}. This is not allowed in strict mode when create_graph=True."
                    )
                else:
                    raise RuntimeError(
                        "The hessian of the user-provided function is independent of "
                        f"input {i}. This is not allowed in strict mode when create_graph=True."
                    )

        res += (grads_i,)

    return res
def _preserve_requires_grad_pass(
    gm: torch.fx.GraphModule,
    sig: ExportGraphSignature,
    fake_params_buffers: dict[str, torch.Tensor],
    constants: dict[str, _ConstantAttributeType],
    flat_fake_args: list[Any],
):
    placeholders = [node for node in gm.graph.nodes if node.op == "placeholder"]
    if len(sig.input_specs) != len(placeholders):
        raise AssertionError(
            f"input_specs length {len(sig.input_specs)} does not match placeholders length {len(placeholders)}"
        )
    i = 0
    for node, spec in zip(placeholders, sig.input_specs):
        if spec.kind in (
            InputKind.PARAMETER,
            InputKind.BUFFER,
        ):
            if spec.target is None:
                raise AssertionError(
                    f"spec.target must not be None for kind {spec.kind}"
                )
            node.meta["val"].requires_grad = fake_params_buffers[
                spec.target
            ].requires_grad
        elif spec.kind == InputKind.USER_INPUT:
            fake_arg = flat_fake_args[i]
            if isinstance(fake_arg, torch.Tensor):
                node.meta["val"].requires_grad = fake_arg.requires_grad
            i += 1
        elif spec.kind == InputKind.CONSTANT_TENSOR:
            if spec.target is None:
                raise AssertionError(
                    "spec.target must not be None for CONSTANT_TENSOR kind"
                )
            constant = constants[spec.target]
            if isinstance(constant, torch.Tensor):
                # If the tensor is not leaf, it should already have a correct requires grad field
                if node.meta["val"].is_leaf:
                    node.meta["val"].requires_grad = constant.requires_grad
                else:
                    if node.meta["val"].requires_grad != constant.requires_grad:
                        raise AssertionError(
                            f"node requires_grad {node.meta['val'].requires_grad} does not match "
                            f"constant requires_grad {constant.requires_grad}"
                        )
        elif spec.kind in (InputKind.CUSTOM_OBJ, InputKind.TOKEN):
            continue
        else:
            raise AssertionError(spec.kind)
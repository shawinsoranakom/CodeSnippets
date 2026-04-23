def shape_env_from_inputs(inputs: Sequence[InputType]) -> ShapeEnv | None:
    fake_mode = detect_fake_mode(inputs)

    # TODO(voz): It would be nice to enable this assert, but there are lots of tests that
    # pass in real inputs for now.
    # if len(inputs) > 0:
    # assert fake_mode is not None, breakpoint()

    if fake_mode is not None:
        return fake_mode.shape_env

    # When there are no tensor inputs, get shape_env from the first SymInt.
    for input in inputs:
        if isinstance(input, torch.SymInt):
            return input.node.shape_env

        # Check tensor sizes and strides for SymInt values
        if isinstance(input, torch.Tensor):
            for size in input.size():
                if isinstance(size, torch.SymInt):
                    return size.node.shape_env
            for stride in input.stride():
                if isinstance(stride, torch.SymInt):
                    return stride.node.shape_env

    # TODO(voz): Should we always have one anyway?
    return None
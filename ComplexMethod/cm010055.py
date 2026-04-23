def detect_fake_mode(inputs: Any = None) -> FakeTensorMode | None:
    """
    Attempts to "detect" what the current fake mode is.  If there is one ambiently
    available from TracingContext, we preferentially use that.  Otherwise, we
    heuristically detect the fake mode via the following sources, in order of
    priority:

        - Currently active fake mode on stack
        - Fake mode associated with passed in tensors (inputs does not
          have to be flattened)
    """
    from torch._subclasses.fake_tensor import (
        FakeTensor,
        FakeTensorMode,
        get_plain_tensors,
    )

    # If TracingContext has a fake_mode, use it authoritatively.
    # This is the case when Dynamo is driving compilation - any fake tensors
    # from other modes in the inputs will be refakified by the caller.
    if context := TracingContext.try_get():
        fake_mode = context.fake_mode
        if fake_mode is not None:
            return fake_mode

    fake_modes = []

    from torch.utils._python_dispatch import _get_current_dispatch_mode_stack

    for i, m in enumerate(reversed(_get_current_dispatch_mode_stack())):
        if isinstance(m, FakeTensorMode):
            fake_modes.append((m, "active fake mode", i))

    flat_inputs = pytree.tree_leaves(inputs)
    for i, flat_input in enumerate(flat_inputs):
        if isinstance(flat_input, FakeTensor):
            fake_modes.append((flat_input.fake_mode, "fake tensor input", i))
        if is_traceable_wrapper_subclass(flat_input):
            out: list[torch.Tensor | int | torch.SymInt] = []
            get_plain_tensors(flat_input, out=out)  # type: ignore[arg-type]
            fake_tensors: list[FakeTensor] = [
                x for x in out if isinstance(x, FakeTensor)
            ]
            fake_modes.extend(
                [
                    (tensor.fake_mode, f"subclass input {i}", ix)
                    for ix, tensor in enumerate(fake_tensors)
                ]
            )

    if fake_modes:
        fake_mode, desc1, i1 = fake_modes[0]
        for m, desc2, i2 in fake_modes[1:]:
            if fake_mode is not m:
                raise AssertionError(
                    f"fake mode ({fake_mode}) from {desc1} {i1} doesn't match mode ({m}) from {desc2} {i2}\n\n"
                    f"fake mode from {desc1} {i1} allocated at:\n{fake_mode.stack}\n"
                    f"fake mode from {desc2} {i2} allocated at:\n{m.stack}"
                )

        return fake_mode
    else:
        return None
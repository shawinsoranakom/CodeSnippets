def cat(tensors: TensorSequenceType, dim: int = 0) -> TensorLikeType:
    def cat_compute_output_memory_format(inputs):
        format = None
        for t in inputs:
            f = utils.suggest_memory_format(t)
            if f == torch.contiguous_format:
                return f
            if format is not None and format != f:
                return torch.contiguous_format
            format = f
        if format is None:
            raise AssertionError("format should not be None if len(inputs) > 0")
        return format

    if len(tensors) == 0:
        msg = "cat expects at least one tensor, but received zero!"
        raise ValueError(msg)

    for tensor in tensors:
        if not isinstance(tensor, TensorLike):
            raise AssertionError(f"tensor must be TensorLike, got {type(tensor)}")

    utils.check_same_device(*tensors, allow_cpu_scalar_tensors=False)

    from torch.fx.experimental.symbolic_shapes import guard_or_false

    # This is a bit tricky.  Naively, you would expect to just pick one
    # arbitrary tensor and check that all tensors match this tensor.  However,
    # there is legacy behavior which says that if you have a 1-D empty tensor
    # (0,), this is permissible.  So you can't assume that all the tensors
    # have same dimensionality, and you can't assume that the first tensor is
    # the correct stencil.
    #
    # We'll implement this in a few passes.  First, we will try to infer the
    # ndim of the cat output.  If this ndim != 1, then we know that all ndim =
    # 1 inputs must be empty, or are errors.  If this ndim == 1, then life
    # is easy (the legacy special case coincides with regular handling).
    #
    # NB: The regular implementation of cat just filters out empty inputs,
    # but we do it slightly different here for better handling for unbacked
    # SymInts

    example = None
    # pyrefly: ignore [bad-assignment]
    for i, t in enumerate(tensors):
        if example is None:
            if t.ndim != 1:
                example = t
        else:
            if t.ndim != 1:
                torch._check(
                    t.ndim == example.ndim,
                    lambda: "Number of dimensions of tensors must match.  "
                    f"Expected {example.ndim}-D tensors, but got {t.ndim}-D for "
                    f"tensor number {i} in the list",
                )

    if example is None:
        # example is None if everything is 1-D.  If so, just arbitrarily pick
        # the first one
        example = tensors[0]

    shape = example.shape
    filtered = []
    for tensor_idx, tensor in enumerate(tensors):
        if len(shape) != len(tensor.shape):
            if tensor.ndim != 1:
                raise AssertionError(
                    f"tensor.ndim should be 1 at this point, got {tensor.ndim}"
                )
            # Don't suggest the legacy behavior in the error message
            torch._check(
                # NB: it is not enough to simply assert that tensor.shape[0] == 0;
                # this MUST be true even under guard size oblivious.
                # Effectively, we must actually know that the shape is zero,
                # passing an unbacked SymInt which we will defer a runtime
                # assert on won't cut it.  This is a policy decision (size
                # oblivious semantics say that u0 tensors never are inferred
                # to be zero size, even if they must be that for the cat to go
                # through), and is load bearing for our Inductor lowerings
                # (which assume that size oblivious tests are OK to determine
                # if a shape is permissibly zero.)
                guard_or_false(tensor.shape[0] == 0),
                lambda: f"Number of dimensions of tensors must match.  "
                f"Expected {example.ndim}-D tensors, but got 1-D for "
                f"tensor number {tensor_idx} in the list",
            )
        else:
            # Remove inputs that are 1-D, zero size
            if tensor.ndim == 1 and guard_or_false(tensor.shape[0] == 0):
                continue
            # Don't bother checking size match, prims.cat will handle it
            filtered.append(tensor)

    memory_format = cat_compute_output_memory_format(tensors)

    if len(filtered) == 0:
        t = tensors[0]

        # TODO: fix this to work with meta tensors
        try:
            # BUG? This looks like it wants to call builtins.any() but is
            # actually calling .any() (in this file). Changing to builtins.any()
            # causes tests to fail:
            # PYTORCH_OPINFO_SAMPLE_INPUT_INDEX=4 python test/test_ops.py -k \
            #   TestFakeTensorCUDA.test_fake_crossref_backward_amp_cat_cuda_float32
            requires_grad = bool(any(x.requires_grad for x in tensors))  # type: ignore[arg-type]
        except Exception:
            requires_grad = False  # type: ignore[assignment]

        return empty(
            (0,),
            dtype=t.dtype,
            device=t.device,
            requires_grad=requires_grad,
            memory_format=memory_format,
        )

    dim = utils.canonicalize_dim(filtered[0].ndim, dim)
    utils.validate_idx(filtered[0].ndim, dim)

    return prims.cat(filtered, dim).clone(memory_format=memory_format)
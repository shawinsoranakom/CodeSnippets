def error_inputs_narrow_narrow_copy(op_info, device, *, is_narrow, is_ref):
    make_arg = partial(make_tensor, device=device, dtype=torch.float32)

    # 0-dim
    yield ErrorInput(SampleInput(make_arg(()), 0, 0, 1),
                     error_type=RuntimeError,
                     error_regex=r"narrow\(\) cannot be applied to a 0-dim tensor\.")

    # out of bounds dim
    if not is_narrow and not is_ref and torch.device(device).type == 'cpu':
        # narrow_copy_dense_cpu_out
        yield ErrorInput(SampleInput(make_arg((M, S, L)), 3, 0, 0),
                         error_type=RuntimeError,
                         error_regex=r"Expected dim < static_cast<int64_t>\(self_sizes.size\(\)\) to be true, but got false\.")
    else:
        yield ErrorInput(SampleInput(make_arg((M, S, L)), 3, 0, 0),
                         error_type=IndexError,
                         error_regex=r"Dimension out of range \(expected to be in range of \[-3, 2\], but got 3\)")
    # out of bounds dim (negative)
    yield ErrorInput(SampleInput(make_arg((L, S, M)), -4, 0, 0),
                     error_type=IndexError,
                     error_regex=r"Dimension out of range \(expected to be in range of \[-3, 2\], but got -4\)")

    # out of bounds start
    yield ErrorInput(SampleInput(make_arg((L, M, S)), 1, M + 1, 0),
                     error_type=IndexError,
                     error_regex=r"start out of range \(expected to be in range of \[-10, 10\], but got 11\)")
    # out of bounds start (negative)
    yield ErrorInput(SampleInput(make_arg((L, M, S)), 1, -M - 1, 0),
                     error_type=IndexError,
                     error_regex=r"start out of range \(expected to be in range of \[-10, 10\], but got -11\)")

    # out of bounds length
    yield ErrorInput(SampleInput(make_arg((S, L, M)), 2, 0, M + 1),
                     error_type=RuntimeError,
                     error_regex=r"start \(0\) \+ length \(11\) exceeds dimension size \(10\)\.")
    # out of bounds length (negative)
    if not is_narrow and not is_ref and torch.device(device).type == 'cpu':
        # narrow_copy_dense_cpu_out
        yield ErrorInput(SampleInput(make_arg((M,)), 0, 0, -1),
                         error_type=RuntimeError,
                         error_regex=r"start \(0\) \+ length \(-1\) exceeds dimension size \(10\)\.")
    else:
        yield ErrorInput(SampleInput(make_arg((M,)), 0, 0, -1),
                         error_type=RuntimeError,
                         error_regex=r"narrow\(\): length must be non-negative\.")

    # Test Tensor overload that was added for XLA. Start must be an 0-dim
    # integral Tensor. narrow_copy doesn't have this overload.
    # https://github.com/pytorch/pytorch/issues/31558
    if is_narrow:
        # *1-dim* integral Tensor
        yield ErrorInput(SampleInput(make_arg((L, M, S)), 1, make_arg(S, dtype=torch.int), 2),
                         error_type=RuntimeError,
                         error_regex=r"start must be an 0-dim integral Tensor\.")

        # 0-dim *bool* Tensor (bools are not allowed)
        yield ErrorInput(SampleInput(make_arg((L, M, S)), -3, make_arg((), dtype=torch.bool), 3),
                         error_type=RuntimeError,
                         error_regex=r"start must be an 0-dim integral Tensor\.")
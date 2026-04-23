def adaptive_avg_pool2d(input: Tensor, output_size: tuple[int, int]):
    # Preconditions
    device = input.device
    shape = input.shape
    ndim = len(shape)
    torch._check(
        ndim in (3, 4),
        lambda: f"adaptive_avg_pool2d(): Expected 3D or 4D tensor, but got {ndim}",
    )
    for d in input.shape[-2:]:
        torch._check(
            d != 0,
            lambda: "adaptive_avg_pool2d(): Expected input to have non-zero size for "
            f"non-batch dimensions, but input has shape {tuple(shape)}.",
        )

    # Optimisation (we should also do this in the kernel implementation)
    if shape[-2] % output_size[-2] == 0 and shape[-1] % output_size[-1] == 0:
        stride = tuple(i // o for i, o in zip(shape[-2:], output_size))
        kernel = tuple(
            i - (o - 1) * s for i, o, s in zip(shape[-2:], output_size, stride)
        )
        return torch.nn.functional.avg_pool2d(input, kernel, stride)

    def start_index(a, b, c):
        return torch.div(a * c, b, rounding_mode="trunc")

    def end_index(a, b, c):
        return torch.div((a + 1) * c + b - 1, b, rounding_mode="trunc")

    def compute_idx(in_size, out_size):
        orange = torch.arange(out_size, device=device, dtype=torch.int64)
        i0 = start_index(orange, out_size, in_size)
        # Let length = end_index - start_index, i.e. the length of the pooling kernels
        # length.max() can be computed analytically as follows:
        maxlength = in_size // out_size + 1
        in_size_mod = in_size % out_size
        # adaptive = True iff there are kernels with different lengths
        adaptive = not (in_size_mod == 0 or out_size % in_size_mod == 0)
        if adaptive:
            maxlength += 1
        elif in_size_mod == 0:
            maxlength -= 1

        range_max = torch.arange(maxlength, device=device, dtype=torch.int64)
        idx = i0.unsqueeze(-1) + range_max
        if adaptive:
            # Need to clamp to avoid accessing out-of-bounds memory
            # TODO make minimum accept scalars
            maxval = torch.scalar_tensor(
                in_size - 1, dtype=idx.dtype, device=idx.device
            )
            idx = torch.minimum(idx, maxval)

            # Compute the length
            i1 = end_index(orange, out_size, in_size)
            length = i1 - i0
        else:
            length = maxlength
        return idx, length, range_max, adaptive

    # length is not None if it's constant, otherwise we'll need to compute it
    idxh, length_h, range_max_h, adaptive_h = compute_idx(shape[-2], output_size[-2])
    idxw, length_w, range_max_w, adaptive_w = compute_idx(shape[-1], output_size[-1])

    vals = input[..., _unsqueeze_to_dim(idxh, 4), idxw]
    # Shortcut for the simpler case
    if not adaptive_h and not adaptive_w:
        return torch.mean(vals, dim=(-3, -1))

    def maybe_mask(vals, length, range_max, adaptive, dim):
        if isinstance(length, IntLike):
            return vals, length
        else:
            # zero-out the things we didn't really want to select
            if dim >= 0:
                raise AssertionError(f"dim should be negative when masking, got {dim}")
            # hack
            mask = range_max >= length.unsqueeze(-1)
            if dim == -2:
                mask = _unsqueeze_to_dim(mask, 4)
            vals = torch.masked_fill(vals, mask, 0.0)
            # Compute the length of each window
            length = _unsqueeze_to_dim(length, -dim)
            return vals, length

    vals, length_h = maybe_mask(
        vals, length_h, range_max_h, adaptive=adaptive_h, dim=-2
    )
    vals, length_w = maybe_mask(
        vals, length_w, range_max_w, adaptive=adaptive_w, dim=-1
    )

    # We unroll the sum as we assume that the kernels are going to be small
    ret = None
    for i, j in product(range(vals.shape[-3]), range(vals.shape[-1])):
        if ret is None:
            ret = vals[..., i, :, j]
        else:
            ret = ret + vals[..., i, :, j]
    return ret / (length_h * length_w)
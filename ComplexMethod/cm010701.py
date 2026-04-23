def _grid_sampler_2d(
    a: Tensor,
    grid: Tensor,
    interpolation_mode: int = 0,
    padding_mode: int = 0,
    align_corners: bool = False,
    _expand_grid: bool = True,
) -> Tensor:
    # This method is a copy of grid_sampler_2d implementation and introduced with additional arg _expand_grid to
    # optionally expand the input grid for performance reasons.
    # Experimenting locally it was found that compiled CUDA code is accelerated by ~5x
    # and CPU code by ~2x on bicubic mode, if we expand the grid from (N, H, W, 2) into (N, C, H, W, 2)
    # However, this leads to a slowdown around ~0.8x on CPU bilinear mode, channels first.
    # Thus we apply this hack to not expand the grid for this case.

    torch._check(
        interpolation_mode in (0, 1, 2),
        lambda: f"Invalid interpolation mode {interpolation_mode}",
    )
    torch._check(
        padding_mode in (0, 1, 2), lambda: f"Invalid padding mode {padding_mode}"
    )

    def unnormalize(coords: Tensor, size: int) -> Tensor:
        # Rescale coordinates from [-1, 1] to:
        #   [0, size - 1] if align_corners is True
        #   [-.5, size -.5] if align_corners is False
        mul = (size * 0.5 - 0.5) if align_corners else (size * 0.5)
        ofs = size * 0.5 - 0.5
        return coords * mul + ofs

    # Reflects coordinates until they fall between low and high (inclusive).
    # The bounds are passed as twice their value so that half-integer values
    # can be represented as ints.
    def reflect_coordinates(coords: Tensor, twice_low: int, twice_high: int) -> Tensor:
        if twice_low == twice_high:
            return torch.zeros_like(coords)
        coords_min = twice_low / 2
        coords_span = (twice_high - twice_low) / 2
        coords2 = (coords - coords_min).abs()
        extra = torch.fmod(coords2, coords_span)
        flips = (coords2 / coords_span).floor().to(dtype=torch.int8)
        return torch.where(
            flips & 1 == 0, extra + coords_min, coords_span + coords_min - extra
        )

    def compute_coordinates(coords: Tensor, size: int) -> Tensor:
        if padding_mode == 0:  # Zero
            return coords
        elif padding_mode == 1:  # Borders
            return torch.clamp(coords, 0, size - 1)
        else:  # padding_mode == 2, Reflection
            if align_corners:
                coords_reflected = reflect_coordinates(coords, 0, 2 * (size - 1))
            else:
                coords_reflected = reflect_coordinates(coords, -1, 2 * size - 1)
            return torch.clamp(coords_reflected, 0, size - 1)

    def compute_source_index(coords: Tensor, size: int) -> Tensor:
        coords_un = unnormalize(coords, size)
        return compute_coordinates(coords_un, size)

    N, C, iH, iW = a.shape
    _, oH, oW, two = grid.shape
    if two != 2:
        raise AssertionError(
            f"grid last dimension must be 2 (for x,y coords), got {two}"
        )

    if _expand_grid:
        # Let's expand grid to [N, C, oH, oW, 2]
        # This allows to generate a single triton cuda kernel instead of two kernels.
        # Two kernels are due source indices, weights have shape (N, 1, oH, oW), xnumel=N*oH*oW
        # and output has shape (N, C, oH, oW), xnumel=N*C*oH*oW
        # Expanding grid to (N, C, oH, oW, two) unifies xnumel to N*C*oH*oW
        grid = grid.view(N, 1, oH, oW, two).expand(N, C, oH, oW, 2)

    def in_bounds_cond(xs: Tensor, ys: Tensor) -> Tensor:
        return torch.logical_and(
            0 <= xs, torch.logical_and(xs < iW, torch.logical_and(0 <= ys, ys < iH))
        )

    N_idx = torch.arange(N, device=a.device).view(N, 1, 1, 1)
    C_idx = torch.arange(C, device=a.device).view(1, C, 1, 1)

    def clip(xs: Tensor, ys: Tensor, ws: Tensor) -> TensorSequenceType:
        cond = in_bounds_cond(xs, ys)
        # To clip to inside valid coordinates, we map the coordinates
        # to (x, y) = (0, 0) and also set the weight to 0
        # We also change the shape of the tensor to the appropriate one for
        # broadcasting with N_idx, C_idx for the purposes of advanced indexing
        c = C if _expand_grid else 1
        return tuple(
            torch.where(cond, t, 0).view(N, c, oH, oW)
            for t in (xs.to(dtype=torch.int64), ys.to(dtype=torch.int64), ws)
        )

    def get_summand(ix: Tensor, iy: Tensor, w) -> Tensor:
        # Perform clipping, index into input tensor and multiply by weight
        idx_x, idx_y, w_ = clip(ix, iy, w)
        return a[N_idx, C_idx, idx_y, idx_x] * w_

    x = grid[..., 0]
    y = grid[..., 1]

    if interpolation_mode == 0:  # Bilinear
        ix = compute_source_index(x, iW)
        iy = compute_source_index(y, iH)

        ix_nw, iy_nw = ix.floor(), iy.floor()
        ix_ne, iy_ne = ix_nw + 1, iy_nw
        ix_sw, iy_sw = ix_nw, iy_nw + 1
        ix_se, iy_se = ix_ne, iy_sw

        w_nw = (ix_se - ix) * (iy_se - iy)
        w_ne = (ix - ix_sw) * (iy_sw - iy)
        w_sw = (ix_ne - ix) * (iy - iy_ne)
        w_se = (ix - ix_nw) * (iy - iy_nw)

        return _sum_tensors(
            get_summand(ix, iy, w)
            for (ix, iy, w) in (
                (ix_nw, iy_nw, w_nw),
                (ix_ne, iy_ne, w_ne),
                (ix_sw, iy_sw, w_sw),
                (ix_se, iy_se, w_se),
            )
        )
    elif interpolation_mode == 1:  # Nearest
        ix = compute_source_index(x, iW)
        iy = compute_source_index(y, iH)

        ix_nearest = ix.round()
        iy_nearest = iy.round()

        return get_summand(ix_nearest, iy_nearest, 1)
    else:  # interpolation_mode == 2, Bicubic
        ix = unnormalize(x, iW)
        iy = unnormalize(y, iH)

        ix_nw = ix.floor()
        iy_nw = iy.floor()

        tx = ix - ix_nw
        ty = iy - iy_nw

        if not _expand_grid:
            tx = tx.unsqueeze(1)
            ty = ty.unsqueeze(1)

        def get_value_bounded(ix: Tensor, iy: Tensor) -> Tensor:
            x = compute_coordinates(ix, iW)
            y = compute_coordinates(iy, iH)
            return get_summand(x, y, 1)

        def get_coeff(ofs: int) -> Tensor:
            iy_ofs = iy_nw + (ofs - 1)
            cs = (
                get_value_bounded(ix_nw - 1, iy_ofs),
                get_value_bounded(ix_nw, iy_ofs),
                get_value_bounded(ix_nw + 1, iy_ofs),
                get_value_bounded(ix_nw + 2, iy_ofs),
            )
            return _upsample_cubic_interp1d(cs, tx)

        coeffs = tuple(get_coeff(ofs) for ofs in range(4))
        return _upsample_cubic_interp1d(coeffs, ty)
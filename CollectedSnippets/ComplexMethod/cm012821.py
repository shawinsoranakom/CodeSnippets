def pallas_compute_tiling(
    ref_shape: tuple[int, ...],
    transpose: bool = False,  # constrain tile size for pallas_permute VMEM
    skip_last_n: int = 0,
    exact_only: bool = False,
    is_tpu: bool = False,
    permutations: list[tuple[int, ...]] | None = None,
    max_grid_product: int | None = None,
) -> tuple[tuple[int, ...], tuple[int, ...], dict[int, int]]:
    """Compute tile shape, grid and axis→grid-dim mapping for CPU/TPU.

    Always uses TPU-compatible alignment (last dim multiple of 128,
    second-to-last multiple of 8) so that the same generated kernel works
    on both CPU-interpret and real TPU.

    *transpose* constrains tile sizes to keep VMEM usage within safe
    limits for pallas_permute (gather-based permutation).

    *skip_last_n* prevents tiling the last N dimensions (used when those
    dims correspond to internal reduction ranges that must remain full).

    *exact_only* restricts tiling to dimensions that divide evenly by the
    tile size (no remainder blocks).  Required on TPU where Mosaic needs
    block shapes to match the XLA memory layout.

    Returns ``(tile_shape, grid, axis_to_grid)`` where *axis_to_grid*
    maps each tiled reference-shape axis index to its position in the
    grid tuple.

    When no dimension benefits from tiling the grid is ``(1,)`` and the
    tile covers the full tensor.
    """
    nd = len(ref_shape)
    if nd == 0:
        return (), (1,), {}

    # Effective number of dims eligible for tiling
    tileable_nd = nd - skip_last_n

    tile = list(ref_shape)
    grid_parts: list[int] = []
    axis_to_grid: dict[int, int] = {}  # ref axis → grid dim

    # Pick alignment based on the physical position of the axis in the
    # tensor, not its position in the tileable subset.  The TPU requires
    # the physical last dim to be a multiple of 128 and the physical
    # second-to-last dim to be a multiple of 8.
    #
    # When permutations are present, an output dim `ax` maps to input
    # dim `perm[ax]`.  If `perm[ax]` is the input's last dim, that
    # output dim must also satisfy _TPU_ALIGN_LAST.  Compute the
    # strictest alignment across all buffers.
    def _input_align(input_ax: int, input_nd: int) -> int:
        return _TPU_ALIGN_LAST if input_ax == input_nd - 1 else _TPU_ALIGN_SECOND_LAST

    def _align(ax: int) -> int:
        out_align = _TPU_ALIGN_LAST if ax == nd - 1 else _TPU_ALIGN_SECOND_LAST
        if permutations:
            for perm in permutations:
                if perm is not None and len(perm) == nd:
                    in_ax = perm[ax]
                    in_align = _input_align(in_ax, len(perm))
                    out_align = max(out_align, in_align)
        return out_align

    def _can_tile_ax(ax: int, dim: int, t: int) -> bool:
        """Check if tiling dim to t is valid."""
        if t >= dim:
            # For TPU padding, we allow tiles >= dimension for the aligned axes
            if _align(ax) == _TPU_ALIGN_LAST or _align(ax) == _TPU_ALIGN_SECOND_LAST:
                return True
            return False
        if exact_only and dim % t != 0:
            if _align(ax) == _TPU_ALIGN_LAST or _align(ax) == _TPU_ALIGN_SECOND_LAST:
                # TPU DMA `#tpu.element_window` natively masks out-of-bounds remainder tiles
                return True
            return False
        return True

    # Second-to-last tileable dim (added first so it becomes grid dim 0)
    if tileable_nd >= 2:
        ax = tileable_nd - 2
        t = _pallas_tile_size(ref_shape[ax], _align(ax), is_tpu=is_tpu)
        if _can_tile_ax(ax, ref_shape[ax], t):
            tile[ax] = t
            axis_to_grid[ax] = len(grid_parts)
            grid_parts.append((ref_shape[ax] + t - 1) // t)

    # Last tileable dim
    if tileable_nd >= 1:
        ax = tileable_nd - 1
        t = _pallas_tile_size(ref_shape[ax], _align(ax), is_tpu=is_tpu)
        if _can_tile_ax(ax, ref_shape[ax], t):
            tile[ax] = t
            axis_to_grid[ax] = len(grid_parts)
            grid_parts.append((ref_shape[ax] + t - 1) // t)

    # When transpose is active, tile dimensions to keep the total tile
    # elements below the safe threshold for Mosaic's permute_dims.
    # Mosaic pads the last dimension to _TPU_ALIGN_LAST (128 for f32),
    # so when the last dim is small (e.g. 2), VMEM usage is much higher
    # than the logical tile size.  We compute an effective element count
    # that accounts for this padding.
    if transpose:
        tile_elems = 1
        for t in tile:
            tile_elems *= t
        last_dim = tile[nd - 1] if nd > 0 else 1
        padded_last = max(last_dim, _TPU_ALIGN_LAST)
        # pallas_permute decomposes ndim>2 permutations by looping over
        # the smallest dim and recursing, creating (ndim-1)-D intermediates
        # at each level.  Mosaic pads the last physical dim of each
        # intermediate to _TPU_ALIGN_LAST (128), which can cause VMEM OOM
        # when a small dim (e.g. 4) ends up as the last dim.
        #
        # For ndim >= 3, compute effective_max from the worst-case VMEM
        # of the (ndim-1)-D intermediate created by pallas_permute.
        # The intermediate removes the loop dim (smallest output dim) and
        # may have a small dim as its last physical dim -> padded to 128.
        if nd >= 4:
            # For 4D+, pallas_permute creates (nd-1)-D intermediates
            # that can have small dims as their last physical dim,
            # which Mosaic pads to _TPU_ALIGN_LAST (128).  This can
            # cause VMEM OOM.  (3D pallas_permute only creates 2D
            # intermediates which Mosaic handles efficiently.)
            sorted_dims = sorted(tile)
            # The loop dim is the smallest; intermediate has the rest.
            inter_dims = sorted_dims[1:]  # (nd-1) dims, sorted
            smallest_inter = inter_dims[0]
            # Padded intermediate: smallest remaining dim padded to 128.
            padded_inter_elems = 1
            for d in inter_dims:
                padded_inter_elems *= d
            pad_factor = max(smallest_inter, _TPU_ALIGN_LAST) // max(smallest_inter, 1)
            padded_inter_elems *= pad_factor
            padded_inter_bytes = padded_inter_elems * 4
            # Conservative VMEM budget: 2MB per intermediate buffer.
            # pallas_permute creates multiple live intermediates (input
            # slices, sub-permutation results, stack temps).  Empirically,
            # 2MB per worst-case intermediate avoids OOM on TPU v4 (64MB VMEM).
            vmem_per_buf = 2 * 1024 * 1024  # 2MB
            if padded_inter_bytes > vmem_per_buf:
                scale = vmem_per_buf / padded_inter_bytes
                effective_max = max(int(tile_elems * scale), 1024)
            else:
                effective_max = _PERMUTE_MAX_TILE_ELEMS
        else:
            # For ndim <= 3: pallas_permute creates 2D intermediates
            # (fine) but jnp.stack creates a 3D result with the same
            # shape as the output.  If the last dim is small, Mosaic
            # pads it to _TPU_ALIGN_LAST (128), which can exhaust VMEM.
            # Empirically: 8MB per padded buffer keeps us safe on TPU v4
            # (64MB VMEM, multiple buffers live simultaneously).
            vmem_per_buf = 8 * 1024 * 1024  # 8MB
            max_nonlast_product = vmem_per_buf // (padded_last * 4)
            effective_max = min(
                max_nonlast_product * last_dim,
                _PERMUTE_MAX_TILE_ELEMS,
            )
        effective_max = min(effective_max, _PERMUTE_MAX_TILE_ELEMS)
        effective_max = max(effective_max, 1024)

        if tile_elems > effective_max:
            # Collect tileable dims.  For ndim >= 4 with VMEM-constrained
            # intermediates, include ALL tileable dims (even the last)
            # since we may need to shrink every dim to fit in VMEM.
            # For ndim <= 3, exclude the last dim (it's often small
            # and already at minimum).
            if nd >= 4:
                tileable_axes = [
                    ax for ax in range(tileable_nd - 1, -1, -1) if ref_shape[ax] > 1
                ]
            else:
                tileable_axes = [
                    ax for ax in range(tileable_nd - 2, -1, -1) if ref_shape[ax] > 1
                ]
            # Distribute reduction proportionally across dims.
            reduction = tile_elems / effective_max
            n = len(tileable_axes)
            per_dim = reduction ** (1.0 / max(n, 1))

            for ax in tileable_axes:
                if tile_elems <= effective_max:
                    break
                dim = ref_shape[ax]
                cur_t = tile[ax]
                align = _align(ax)
                # Target tile: proportional reduction, but also check
                # against the remaining budget for subsequent dims.
                target = int(cur_t / per_dim)
                remaining_budget = effective_max * cur_t // tile_elems
                target = min(target, remaining_budget)
                target = (target // align) * align
                target = max(target, align)
                # Find largest aligned divisor of dim <= target.
                best_t = cur_t
                for candidate in range(target, 0, -align):
                    if candidate >= cur_t:
                        continue
                    if dim % candidate != 0:
                        continue
                    best_t = candidate
                    break
                if best_t < cur_t:
                    if ax in axis_to_grid:
                        grid_parts[axis_to_grid[ax]] = dim // best_t
                    else:
                        axis_to_grid[ax] = len(grid_parts)
                        grid_parts.append(dim // best_t)
                    tile_elems = tile_elems * best_t // cur_t
                    tile[ax] = best_t

    grid = tuple(grid_parts) if grid_parts else (1,)

    # Enforce max_grid_product by scaling up tiles on tiled axes.
    if max_grid_product is not None and grid_parts:
        grid_product = 1
        for g in grid_parts:
            grid_product *= g
        if grid_product > max_grid_product:
            # Sort tiled axes by their grid contribution (descending)
            # and increase tiles to reduce the grid.
            tiled_axes = sorted(
                axis_to_grid.keys(),
                key=lambda ax: grid_parts[axis_to_grid[ax]],
                reverse=True,
            )
            for ax in tiled_axes:
                if grid_product <= max_grid_product:
                    break
                gi = axis_to_grid[ax]
                cur_grid = grid_parts[gi]
                cur_tile = tile[ax]
                dim = ref_shape[ax]
                align = _align(ax)
                # Target grid for this axis: proportional share of reduction
                target_grid = max(1, int(cur_grid * max_grid_product / grid_product))
                target_tile = (dim + target_grid - 1) // target_grid
                # Round up to alignment
                target_tile = ((target_tile + align - 1) // align) * align
                target_tile = min(target_tile, dim)
                # Find smallest aligned value >= target_tile that divides dim
                # (or just use the rounded-up value if exact_only is False)
                best_tile = dim  # fallback: full dim
                if exact_only:
                    for candidate in range(target_tile, dim + 1, align):
                        if dim % candidate == 0:
                            best_tile = candidate
                            break
                else:
                    best_tile = target_tile
                if best_tile > cur_tile:
                    new_grid = (dim + best_tile - 1) // best_tile
                    grid_product = grid_product * new_grid // cur_grid
                    grid_parts[gi] = new_grid
                    tile[ax] = best_tile
            grid = tuple(grid_parts)

    return tuple(tile), grid, axis_to_grid
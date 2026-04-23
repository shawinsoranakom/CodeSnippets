def pallas_make_block_spec(
    buf_shape: tuple[int, ...],
    ref_shape: tuple[int, ...],
    tile_shape: tuple[int, ...],
    axis_to_grid: dict[int, int],
    n_grid: int,
    permutation: tuple[int, ...] | None = None,
    is_output: bool = False,
) -> Any:
    """Build a ``pl.BlockSpec`` for *buf_shape* given tiling of *ref_shape*.

    Lower-ndim buffers are right-aligned with the reference shape (numpy
    broadcast rules).  Dimensions that match a tiled reference dimension
    are tiled; broadcast dimensions (size 1 or absent) are kept full.

    When *buf_nd > ref_nd* (reduction inputs), we find an alignment offset
    so the ref dims map into the buffer.  Extra dims are kept at full size
    with index 0 in the index_map.

    When *permutation* is given (a tuple mapping ref axis -> buf axis),
    the buffer dimensions are accessed in permuted order relative to the
    reference shape.  For example, permutation=(1, 0) swaps the last two.

    When *is_output* is True and *buf_nd < ref_nd*, left-alignment is used
    as a fallback (for reduction outputs whose trailing dims were reduced).
    """
    from jax.experimental import (  # pyrefly: ignore [import-error, missing-import]
        pallas as pl,
    )

    buf_nd = len(buf_shape)
    ref_nd = len(ref_shape)

    if buf_nd == 0:
        # Scalar — untouched regardless of grid shape.
        return pl.BlockSpec((1,), _make_index_map([], 1, n_grid))

    bs = list(buf_shape)
    tiled_pairs: list[tuple[int, int]] = []

    if buf_nd > ref_nd:
        # Reduction input: find alignment offset k where ref dims map into buf.
        align_k = 0
        for k in range(buf_nd - ref_nd + 1):
            ok = True
            for i in range(ref_nd):
                if ref_shape[i] == 1:
                    continue
                if buf_shape[k + i] != ref_shape[i]:
                    ok = False
                    break
            if ok:
                align_k = k
                break

        for ref_ax, grid_dim in axis_to_grid.items():
            buf_ax = align_k + ref_ax
            if 0 <= buf_ax < buf_nd and buf_shape[buf_ax] == ref_shape[ref_ax]:
                bs[buf_ax] = tile_shape[ref_ax]
                tiled_pairs.append((buf_ax, grid_dim))

    elif permutation is not None and buf_nd == ref_nd:
        # Permuted buffer: map ref axes through the permutation.
        for ref_ax, grid_dim in axis_to_grid.items():
            buf_ax = permutation[ref_ax]
            if 0 <= buf_ax < buf_nd and buf_shape[buf_ax] == ref_shape[ref_ax]:
                bs[buf_ax] = tile_shape[ref_ax]
                tiled_pairs.append((buf_ax, grid_dim))

    else:
        # Standard right-alignment, with left-alignment fallback for
        # reduction outputs (e.g. sum(dim=-1) on (10,10) → (10,)).
        for ref_ax, grid_dim in axis_to_grid.items():
            buf_ax = ref_ax - (ref_nd - buf_nd)
            if 0 <= buf_ax < buf_nd and buf_shape[buf_ax] == ref_shape[ref_ax]:
                bs[buf_ax] = tile_shape[ref_ax]
                tiled_pairs.append((buf_ax, grid_dim))
            elif (
                is_output
                and buf_nd < ref_nd
                and 0 <= ref_ax < buf_nd
                and buf_shape[ref_ax] == ref_shape[ref_ax]
            ):
                # Left-aligned match for output: buf dim i matches ref dim i
                # (reduction output whose trailing dims were reduced away)
                bs[ref_ax] = tile_shape[ref_ax]
                tiled_pairs.append((ref_ax, grid_dim))

    return pl.BlockSpec(
        tuple(bs),
        _make_index_map(tiled_pairs, buf_nd, n_grid),
    )
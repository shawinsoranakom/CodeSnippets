def pallas_permute(x, perm):
    """Permute array x according to perm, working around Mosaic TPU bugs.

    Mosaic's jnp.permute_dims produces corrupted output for certain 3D+
    permutations at large sizes.  Decomposes into: loop over smallest output
    dim via unrolled Python loop + stack, with recursive sub-permutation.
    At the 2D base case, uses jnp.permute_dims (which works on Mosaic).

    Callers should ensure tiles are small enough via tiling so that the
    Mosaic bug doesn't trigger (threshold ~ 256K elements).
    """
    import jax.numpy as jnp  # pyrefly: ignore [import-error, missing-import]

    ndim = len(perm)
    if ndim <= 2:
        return jnp.permute_dims(x, perm)
    if perm == tuple(range(ndim)):
        return x  # identity

    shape = x.shape
    out_shape = tuple(shape[p] for p in perm)

    # Choose the output dimension with the smallest size to loop over.
    loop_out_dim = min(range(ndim), key=lambda d: out_shape[d])
    loop_size = out_shape[loop_out_dim]
    loop_in_dim = perm[loop_out_dim]

    # Build the sub-permutation for the remaining (ndim-1) dimensions.
    remaining_in_dims = [d for d in range(ndim) if d != loop_in_dim]
    remaining_out_perm_raw = [perm[d] for d in range(ndim) if d != loop_out_dim]
    dim_map = {old: new for new, old in enumerate(remaining_in_dims)}
    sub_perm = tuple(dim_map[d] for d in remaining_out_perm_raw)

    # Unrolled loop: extract slices with static indices, apply sub-perm,
    # then stack along the loop output dimension.
    slices = []
    # pyrefly: ignore [bad-argument-type]
    for i in range(loop_size):
        idx: list[Any] = [slice(None)] * ndim
        idx[loop_in_dim] = i
        slc = x[tuple(idx)]  # static index, removes loop_in_dim
        slc_p = pallas_permute(slc, sub_perm)
        slices.append(slc_p)

    return jnp.stack(slices, axis=loop_out_dim)
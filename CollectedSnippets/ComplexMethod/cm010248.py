def bsr_scatter_mm(bsr, other, indices_data=None, out=None):
    """BSR @ strided -> strided"""

    if bsr.ndim != 2:
        raise AssertionError(f"bsr must be 2D, got {bsr.ndim}D")
    if other.ndim < 2:
        raise AssertionError(
            f"other must have at least 2 dimensions, got {other.ndim}D"
        )

    Ms, Ks, Ns = bsr.shape[-2], bsr.shape[-1], other.shape[-1]
    blocksize = bsr.values().shape[-2:]

    if indices_data is None:
        indices_data = bsr_scatter_mm_indices_data(
            bsr, other, indices_format="bsr_strided_mm_compressed"
        )

    indices_format = indices_data[0]

    if out is None:
        out = torch.empty(
            (*other.shape[:-2], Ms, Ns), dtype=bsr.dtype, device=bsr.device
        )
    out_shape = out.shape
    out = as1Dbatch(out)

    if bsr._nnz() == 0:
        out.zero_()
    elif indices_format in {"bsr_strided_mm_compressed", "bsr_strided_mm"}:
        out.zero_()
        scatter_mm(bsr.values(), other, indices_data, accumulators=out)
    elif indices_format == "scatter_mm":
        nbatches = other.shape[:-2].numel()
        accumulators = torch.zeros(
            (
                nbatches * Ms // blocksize[0] * Ns // blocksize[0],
                blocksize[0],
                blocksize[0],
            ),
            dtype=bsr.dtype,
            device=bsr.device,
        )
        others = (
            as1Dbatch(other)
            .transpose(-2, -1)
            .view(
                nbatches,
                Ns // blocksize[0],
                blocksize[0],
                Ks // blocksize[1],
                blocksize[1],
            )
            .movedim(
                (3, 1, 4, 2), (1, 2, 3, 4)
            )  # equivalent to .transpose(-3, -2).transpose(-2, -1).transpose(-4, -3)
            .flatten(0, 2)
        )
        scatter_mm(bsr.values(), others, indices_data, accumulators=accumulators)
        out.copy_(
            accumulators.unflatten(
                0, (nbatches, Ms // blocksize[0], Ns // blocksize[0])
            )
            .movedim(
                (1, 2, 3, 4), (3, 1, 4, 2)
            )  # equivalent to .transpose(-4, -3).transpose(-2, -1).transpose(-3, -2)
            .reshape(nbatches, Ns, Ms)
            .transpose(-2, -1)
        )
    else:
        raise NotImplementedError(indices_format)

    return out.view(out_shape)
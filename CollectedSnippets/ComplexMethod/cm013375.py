def fill_diagonal(a: ArrayLike, val: ArrayLike, wrap=False):
    if a.ndim < 2:
        raise ValueError("array must be at least 2-d")
    if val.numel() == 0 and not wrap:
        a.fill_diagonal_(val)
        return a

    if val.ndim == 0:
        val = val.unsqueeze(0)

    # torch.Tensor.fill_diagonal_ only accepts scalars
    # If the size of val is too large, then val is trimmed
    if a.ndim == 2:
        tall = a.shape[0] > a.shape[1]
        # wrap does nothing for wide matrices...
        if not wrap or not tall:
            # Never wraps
            diag = a.diagonal()
            diag.copy_(val[: diag.numel()])
        else:
            # wraps and tall... leaving one empty line between diagonals?!
            max_, min_ = a.shape
            idx = torch.arange(max_ - max_ // (min_ + 1))
            mod = idx % min_
            div = idx // min_
            a[(div * (min_ + 1) + mod, mod)] = val[: idx.numel()]
    else:
        idx = diag_indices_from(a)
        # a.shape = (n, n, ..., n)
        a[idx] = val[: a.shape[0]]

    return a
def choice(a: ArrayLike, size=None, replace=True, p: ArrayLike | None = None):
    # https://stackoverflow.com/questions/59461811/random-choice-with-pytorch
    if a.numel() == 1:
        a = torch.arange(a)

    # TODO: check a.dtype is integer -- cf np.random.choice(3.4) which raises

    # number of draws
    if size is None:
        num_el = 1
    elif _util.is_sequence(size):
        num_el = 1
        for el in size:
            num_el *= el
    else:
        num_el = size

    # prepare the probabilities
    if p is None:
        p = torch.ones_like(a) / a.shape[0]

    # cf https://github.com/numpy/numpy/blob/main/numpy/random/mtrand.pyx#L973
    atol = sqrt(torch.finfo(p.dtype).eps)
    if abs(p.sum() - 1.0) > atol:
        raise ValueError("probabilities do not sum to 1.")

    # actually sample
    indices = torch.multinomial(p, num_el, replacement=replace)

    if _util.is_sequence(size):
        indices = indices.reshape(size)

    samples = a[indices]

    return samples
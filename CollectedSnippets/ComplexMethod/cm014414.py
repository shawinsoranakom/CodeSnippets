def make_grid(I, ncols=8):
    # I: N1HW or N3HW
    if not isinstance(I, np.ndarray):
        raise AssertionError("plugin error, should pass numpy array here")
    if I.shape[1] == 1:
        I = np.concatenate([I, I, I], 1)
    if I.ndim != 4 or I.shape[1] != 3:
        raise AssertionError("Input should be a 4D numpy array with 3 channels")
    nimg = I.shape[0]
    H = I.shape[2]
    W = I.shape[3]
    ncols = min(nimg, ncols)
    nrows = int(np.ceil(float(nimg) / ncols))
    canvas = np.zeros((3, H * nrows, W * ncols), dtype=I.dtype)
    i = 0
    for y in range(nrows):
        for x in range(ncols):
            if i >= nimg:
                break
            canvas[:, y * H : (y + 1) * H, x * W : (x + 1) * W] = I[i]
            i = i + 1
    return canvas
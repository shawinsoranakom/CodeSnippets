def rand_structure(itemsize, valid, maxdim=5, maxshape=16, shape=()):
    """Return random structure:
           (memlen, itemsize, ndim, shape, strides, offset)
       If 'valid' is true, the returned structure is valid, otherwise invalid.
       If 'shape' is given, use that instead of creating a random shape.
    """
    if not shape:
        ndim = randrange(maxdim+1)
        if (ndim == 0):
            if valid:
                return itemsize, itemsize, ndim, (), (), 0
            else:
                nitems = randrange(1, 16+1)
                memlen = nitems * itemsize
                offset = -itemsize if randrange(2) == 0 else memlen
                return memlen, itemsize, ndim, (), (), offset

        minshape = 2
        n = randrange(100)
        if n >= 95 and valid:
            minshape = 0
        elif n >= 90:
            minshape = 1
        shape = [0] * ndim

        for i in range(ndim):
            shape[i] = randrange(minshape, maxshape+1)
    else:
        ndim = len(shape)

    maxstride = 5
    n = randrange(100)
    zero_stride = True if n >= 95 and n & 1 else False

    strides = [0] * ndim
    strides[ndim-1] = itemsize * randrange(-maxstride, maxstride+1)
    if not zero_stride and strides[ndim-1] == 0:
        strides[ndim-1] = itemsize

    for i in range(ndim-2, -1, -1):
        maxstride *= shape[i+1] if shape[i+1] else 1
        if zero_stride:
            strides[i] = itemsize * randrange(-maxstride, maxstride+1)
        else:
            strides[i] = ((1,-1)[randrange(2)] *
                          itemsize * randrange(1, maxstride+1))

    imin = imax = 0
    if not 0 in shape:
        imin = sum(strides[j]*(shape[j]-1) for j in range(ndim)
                   if strides[j] <= 0)
        imax = sum(strides[j]*(shape[j]-1) for j in range(ndim)
                   if strides[j] > 0)

    nitems = imax - imin
    if valid:
        offset = -imin * itemsize
        memlen = offset + (imax+1) * itemsize
    else:
        memlen = (-imin + imax) * itemsize
        offset = -imin-itemsize if randrange(2) == 0 else memlen
    return memlen, itemsize, ndim, shape, strides, offset
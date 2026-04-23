def rand_aligned_slices(maxdim=5, maxshape=16):
    """Create (lshape, rshape, tuple(lslices), tuple(rslices)) such that
       shapeof(x[lslices]) == shapeof(y[rslices]), where x is an array
       with shape 'lshape' and y is an array with shape 'rshape'."""
    ndim = randrange(1, maxdim+1)
    minshape = 2
    n = randrange(100)
    if n >= 95:
        minshape = 0
    elif n >= 90:
        minshape = 1
    all_random = True if randrange(100) >= 80 else False
    lshape = [0]*ndim; rshape = [0]*ndim
    lslices = [0]*ndim; rslices = [0]*ndim

    for n in range(ndim):
        small = randrange(minshape, maxshape+1)
        big = randrange(minshape, maxshape+1)
        if big < small:
            big, small = small, big

        # Create a slice that fits the smaller value.
        if all_random:
            start = randrange(-small, small+1)
            stop = randrange(-small, small+1)
            step = (1,-1)[randrange(2)] * randrange(1, small+2)
            s_small = slice(start, stop, step)
            _, _, _, slicelen = slice_indices(s_small, small)
        else:
            slicelen = randrange(1, small+1) if small > 0 else 0
            s_small = randslice_from_slicelen(slicelen, small)

        # Create a slice of the same length for the bigger value.
        s_big = randslice_from_slicelen(slicelen, big)
        if randrange(2) == 0:
            rshape[n], lshape[n] = big, small
            rslices[n], lslices[n] = s_big, s_small
        else:
            rshape[n], lshape[n] = small, big
            rslices[n], lslices[n] = s_small, s_big

    return lshape, rshape, tuple(lslices), tuple(rslices)
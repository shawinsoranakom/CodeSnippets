def min_scalar_type(a: ArrayLike, /):
    # https://github.com/numpy/numpy/blob/maintenance/1.24.x/numpy/core/src/multiarray/convert_datatype.c#L1288

    from ._dtypes import DType

    if a.numel() > 1:
        # numpy docs: "For non-scalar array a, returns the vector's dtype unmodified."
        return DType(a.dtype)

    if a.dtype == torch.bool:
        dtype = torch.bool

    elif a.dtype.is_complex:
        fi = torch.finfo(torch.float32)
        fits_in_single = a.dtype == torch.complex64 or (
            fi.min <= a.real <= fi.max and fi.min <= a.imag <= fi.max
        )
        dtype = torch.complex64 if fits_in_single else torch.complex128

    elif a.dtype.is_floating_point:
        for dt in [torch.float16, torch.float32, torch.float64]:
            fi = torch.finfo(dt)
            if fi.min <= a <= fi.max:
                dtype = dt
                break
    else:
        # must be integer
        for dt in [torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64]:
            # Prefer unsigned int where possible, as numpy does.
            ii = torch.iinfo(dt)
            if ii.min <= a <= ii.max:
                dtype = dt
                break

    return DType(dtype)
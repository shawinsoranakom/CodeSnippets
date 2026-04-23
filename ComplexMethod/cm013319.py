def dtypes_dispatch_hint(dtypes):
    # Function returns the appropriate dispatch function (from COMPLETE_DTYPES_DISPATCH and EXTENSIBLE_DTYPE_DISPATCH)
    # and its string representation for the passed `dtypes`.
    return_type = collections.namedtuple("return_type", "dispatch_fn dispatch_fn_str")

    # CUDA is not available, dtypes will be empty.
    if len(dtypes) == 0:
        return return_type((), "()")

    set_dtypes = set(dtypes)
    for dispatch in COMPLETE_DTYPES_DISPATCH:
        # Short circuit if we get an exact match.
        if set(dispatch()) == set_dtypes:
            return return_type(dispatch, dispatch.__name__ + "()")

    chosen_dispatch = None
    chosen_dispatch_score = 0.0
    for dispatch in EXTENSIBLE_DTYPE_DISPATCH:
        dispatch_dtypes = set(dispatch())
        if not dispatch_dtypes.issubset(set_dtypes):
            continue

        score = len(dispatch_dtypes)
        if score > chosen_dispatch_score:
            chosen_dispatch_score = score
            chosen_dispatch = dispatch

    # If user passed dtypes which are lower than the lowest
    # dispatch type available (not likely but possible in code path).
    if chosen_dispatch is None:
        return return_type((), str(dtypes))

    return return_type(
        partial(dispatch, *tuple(set(dtypes) - set(dispatch()))),
        dispatch.__name__ + str(tuple(set(dtypes) - set(dispatch()))),
    )
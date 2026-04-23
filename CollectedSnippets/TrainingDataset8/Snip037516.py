def _marshall_any_array(pandas_array, proto_array) -> None:
    """Convert a 1D numpy.Array into a proto.AnyArray.

    pandas_array - 1D arrays which is AnyArray compatible (input).
    proto_array  - proto.AnyArray (output)
    """
    import numpy as np

    # Convert to np.array as necessary.
    if not hasattr(pandas_array, "dtype"):
        pandas_array = np.array(pandas_array)

    # Only works on 1D arrays.
    if len(pandas_array.shape) != 1:
        raise ValueError("Array must be 1D.")

    # Perform type-conversion based on the array dtype.
    if issubclass(pandas_array.dtype.type, np.floating):
        proto_array.doubles.data.extend(pandas_array)
    elif issubclass(pandas_array.dtype.type, np.timedelta64):
        proto_array.timedeltas.data.extend(pandas_array.astype(np.int64))
    elif issubclass(pandas_array.dtype.type, np.integer):
        proto_array.int64s.data.extend(pandas_array)
    elif pandas_array.dtype == np.bool_:
        proto_array.int64s.data.extend(pandas_array)
    elif pandas_array.dtype == np.object_:
        proto_array.strings.data.extend(map(str, pandas_array))
    # dtype='string', <class 'pandas.core.arrays.string_.StringDtype'>
    # NOTE: StringDtype is considered experimental.
    # The implementation and parts of the API may change without warning.
    elif pandas_array.dtype.name == "string":
        proto_array.strings.data.extend(map(str, pandas_array))
    # Setting a timezone changes (dtype, dtype.type) from
    #   'datetime64[ns]', <class 'numpy.datetime64'>
    # to
    #   datetime64[ns, UTC], <class 'pandas._libs.tslibs.timestamps.Timestamp'>
    elif pandas_array.dtype.name.startswith("datetime64"):
        # Just convert straight to ISO 8601, preserving timezone
        # awareness/unawareness. The frontend will render it correctly.
        proto_array.datetimes.data.extend(pandas_array.map(datetime.datetime.isoformat))
    else:
        raise NotImplementedError("Dtype %s not understood." % pandas_array.dtype)
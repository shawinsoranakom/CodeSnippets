def _determine_key_type(key, accept_slice=True):
    """Determine the data type of key.

    Parameters
    ----------
    key : scalar, slice or array-like
        The key from which we want to infer the data type.

    accept_slice : bool, default=True
        Whether or not to raise an error if the key is a slice.

    Returns
    -------
    dtype : {'int', 'str', 'bool', None}
        Returns the data type of key.
    """
    err_msg = (
        "No valid specification of the columns. Only a scalar, list or "
        "slice of all integers or all strings, or boolean mask is "
        "allowed"
    )

    dtype_to_str = {int: "int", str: "str", bool: "bool", np.bool_: "bool"}
    array_dtype_to_str = {
        "i": "int",
        "u": "int",
        "b": "bool",
        "O": "str",
        "U": "str",
        "S": "str",
    }

    if key is None:
        return None
    if isinstance(key, tuple(dtype_to_str.keys())):
        try:
            return dtype_to_str[type(key)]
        except KeyError:
            raise ValueError(err_msg)
    if isinstance(key, slice):
        if not accept_slice:
            raise TypeError(
                "Only array-like or scalar are supported. A Python slice was given."
            )
        if key.start is None and key.stop is None:
            return None
        key_start_type = _determine_key_type(key.start)
        key_stop_type = _determine_key_type(key.stop)
        if key_start_type is not None and key_stop_type is not None:
            if key_start_type != key_stop_type:
                raise ValueError(err_msg)
        if key_start_type is not None:
            return key_start_type
        return key_stop_type
    if isinstance(key, (list, tuple)):
        unique_key = set(key)
        key_type = {_determine_key_type(elt) for elt in unique_key}
        if not key_type:
            return None
        if len(key_type) != 1:
            raise ValueError(err_msg)
        return key_type.pop()
    if hasattr(key, "dtype"):
        xp, is_array_api = get_namespace(key)
        # NumPy arrays are special-cased in their own branch because the Array API
        # cannot handle object/string-based dtypes that are often used to index
        # columns of dataframes by names.
        if is_array_api and not _is_numpy_namespace(xp):
            if xp.isdtype(key.dtype, "bool"):
                return "bool"
            elif xp.isdtype(key.dtype, "integral"):
                return "int"
            else:
                raise ValueError(err_msg)
        else:
            try:
                return array_dtype_to_str[key.dtype.kind]
            except KeyError:
                raise ValueError(err_msg)
    raise ValueError(err_msg)
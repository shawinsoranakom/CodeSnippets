def device(x: _ArrayApiObj, /) -> Device:
    """
    Hardware device the array data resides on.

    This is equivalent to `x.device` according to the `standard
    <https://data-apis.org/array-api/latest/API_specification/generated/array_api.array.device.html>`__.
    This helper is included because some array libraries either do not have
    the `device` attribute or include it with an incompatible API.

    Parameters
    ----------
    x: array
        array instance from an array API compatible library.

    Returns
    -------
    out: device
        a ``device`` object (see the `Device Support <https://data-apis.org/array-api/latest/design_topics/device_support.html>`__
        section of the array API specification).

    Notes
    -----

    For NumPy the device is always `"cpu"`. For Dask, the device is always a
    special `DASK_DEVICE` object.

    See Also
    --------

    to_device : Move array data to a different device.

    """
    if is_numpy_array(x):
        return "cpu"
    elif is_dask_array(x):
        # Peek at the metadata of the Dask array to determine type
        if is_numpy_array(x._meta):
            # Must be on CPU since backed by numpy
            return "cpu"
        return _DASK_DEVICE
    elif is_jax_array(x):
        # FIXME Jitted JAX arrays do not have a device attribute
        #       https://github.com/jax-ml/jax/issues/26000
        #       Return None in this case. Note that this workaround breaks
        #       the standard and will result in new arrays being created on the
        #       default device instead of the same device as the input array(s).
        x_device = getattr(x, "device", None)
        # Older JAX releases had .device() as a method, which has been replaced
        # with a property in accordance with the standard.
        if inspect.ismethod(x_device):
            return x_device()
        else:
            return x_device
    elif is_pydata_sparse_array(x):
        # `sparse` will gain `.device`, so check for this first.
        x_device = getattr(x, "device", None)
        if x_device is not None:
            return x_device
        # Everything but DOK has this attr.
        try:
            inner = x.data  # pyright: ignore
        except AttributeError:
            return "cpu"
        # Return the device of the constituent array
        return device(inner)  # pyright: ignore
    return x.device
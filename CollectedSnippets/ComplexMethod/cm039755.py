def to_device(x: Array, device: Device, /, *, stream: int | Any | None = None) -> Array:
    """
    Copy the array from the device on which it currently resides to the specified ``device``.

    This is equivalent to `x.to_device(device, stream=stream)` according to
    the `standard
    <https://data-apis.org/array-api/latest/API_specification/generated/array_api.array.to_device.html>`__.
    This helper is included because some array libraries do not have the
    `to_device` method.

    Parameters
    ----------

    x: array
        array instance from an array API compatible library.

    device: device
        a ``device`` object (see the `Device Support <https://data-apis.org/array-api/latest/design_topics/device_support.html>`__
        section of the array API specification).

    stream: int | Any | None
        stream object to use during copy. In addition to the types supported
        in ``array.__dlpack__``, implementations may choose to support any
        library-specific stream object with the caveat that any code using
        such an object would not be portable.

    Returns
    -------

    out: array
        an array with the same data and data type as ``x`` and located on the
        specified ``device``.

    Notes
    -----

    For NumPy, this function effectively does nothing since the only supported
    device is the CPU. For CuPy, this method supports CuPy CUDA
    :external+cupy:class:`Device <cupy.cuda.Device>` and
    :external+cupy:class:`Stream <cupy.cuda.Stream>` objects. For PyTorch,
    this is the same as :external+torch:meth:`x.to(device) <torch.Tensor.to>`
    (the ``stream`` argument is not supported in PyTorch).

    See Also
    --------

    device : Hardware device the array data resides on.

    """
    if is_numpy_array(x):
        if stream is not None:
            raise ValueError("The stream argument to to_device() is not supported")
        if device == "cpu":
            return x
        raise ValueError(f"Unsupported device {device!r}")
    elif is_cupy_array(x):
        # cupy does not yet have to_device
        return _cupy_to_device(x, device, stream=stream)
    elif is_torch_array(x):
        return _torch_to_device(x, device, stream=stream)
    elif is_dask_array(x):
        if stream is not None:
            raise ValueError("The stream argument to to_device() is not supported")
        # TODO: What if our array is on the GPU already?
        if device == "cpu":
            return x
        raise ValueError(f"Unsupported device {device!r}")
    elif is_jax_array(x):
        if not hasattr(x, "__array_namespace__"):
            # In JAX v0.4.31 and older, this import adds to_device method to x...
            import jax.experimental.array_api  # noqa: F401  # pyright: ignore

            # ... but only on eager JAX. It won't work inside jax.jit.
            if not hasattr(x, "to_device"):
                return x
        return x.to_device(device, stream=stream)
    elif is_pydata_sparse_array(x) and device == _device(x):
        # Perform trivial check to return the same array if
        # device is same instead of err-ing.
        return x
    return x.to_device(device, stream=stream)
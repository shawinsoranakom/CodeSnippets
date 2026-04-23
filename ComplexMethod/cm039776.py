def capabilities(
    xp: ModuleType, *, device: Device | None = None
) -> dict[str, int | None]:
    """
    Return patched ``xp.__array_namespace_info__().capabilities()``.

    TODO this helper should be eventually removed once all the special cases
    it handles are fixed in the respective backends.

    Parameters
    ----------
    xp : array_namespace
        The standard-compatible namespace.
    device : Device, optional
        The device to use.

    Returns
    -------
    dict
        Capabilities of the namespace.
    """
    out = xp.__array_namespace_info__().capabilities()
    if is_pydata_sparse_namespace(xp):
        if out["boolean indexing"]:
            # FIXME https://github.com/pydata/sparse/issues/876
            # boolean indexing is supported, but not when the index is a sparse array.
            # boolean indexing by list or numpy array is not part of the Array API.
            out = out.copy()
            out["boolean indexing"] = False
    elif is_jax_namespace(xp):
        if out["boolean indexing"]:  # pragma: no cover
            # Backwards compatibility with jax <0.6.0
            # https://github.com/jax-ml/jax/issues/27418
            out = out.copy()
            out["boolean indexing"] = False
    elif is_torch_namespace(xp):
        # FIXME https://github.com/data-apis/array-api/issues/945
        device = xp.get_default_device() if device is None else xp.device(device)
        if device.type == "meta":  # type: ignore[union-attr]  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]
            out = out.copy()
            out["boolean indexing"] = False
            out["data-dependent shapes"] = False

    return out
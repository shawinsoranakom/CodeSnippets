def get_meta(op, key, device_name=None, version=(0, torch.float16, 0.5), exact=False):
    """Return triton kernel meta parameters of the specified op and its inputs key.

    Parameters
    ----------
    op (str): The name of an operation that implementation uses meta parameters.
    key (tuple): A tuple of op input parameters, e.g. shapes, etc.
    device_name (optional, str): The name of a device for which op
      parameters are provided.
    version (optional, hashable): Specifies the version of parameters.
    exact (optional, bool): When True, the returned data (if
      available) corresponds exactly to the specified device_name and
      version information. Otherwise, if the corresponding data is not
      available but there exists a data set that is computed for a
      similar GPU device, then this data set will be returned.

    Returns
    -------
    result (dict): The requested mapping of parameter names and
      values, or None when no data is available. If the input `key`
      contains `"*"`, the result will be a dictionary of keys and
      mappings that match with the given `key`.
    """
    if device_name is None:
        device_name = _get_device_name()

    op_data = _operation_device_version_data.get((op, device_name, version))
    if op_data is None and not exact:
        # A lack of op data could be due to using a (slightly)
        # different GPU model compared to a model for which optimal
        # meta parameters have been computed. In the following we'll
        # assume that there is a set of GPU models that all have
        # a similar set of optimal meta parameters.
        if (
            device_name is not None
            and re.match(r"NVIDIA A100[^\d]", device_name) is not None
        ):
            device_name = "NVIDIA A100-SXM4-80GB"
        else:
            return
        op_data = _operation_device_version_data.get((op, device_name, version))
    if op_data is None:
        return

    matching_data = {}
    if "*" in key:
        for op_key in op_data:
            if [
                None
                for k1, k2 in zip(op_key, key, strict=True)
                if k2 != "*" and k1 != k2
            ]:
                continue
            matching_data[op_key] = op_data[op_key]
    else:
        values = op_data.get(key)
        if values is not None:
            matching_data[key] = values
    matching_meta = {}
    for op_key, values in matching_data.items():
        if op == "scatter_mm":
            names = (
                "GROUP_SIZE",
                "SPLIT_N",
                "TILE_M",
                "TILE_N",
                "num_stages",
                "num_warps",
            )
            meta = dict(zip(names, values, strict=True))
        elif op in {"bsr_dense_addmm", "_int_bsr_dense_addmm"}:
            meta = dict(
                zip(
                    ("GROUP_SIZE_ROW", "SPLIT_N", "num_stages", "num_warps"),
                    values,
                    strict=True,
                )
            )
        else:
            raise NotImplementedError(f"names for {op=}")
        if "*" not in key:
            return meta

        matching_meta[op_key] = meta

    if "*" in key:
        return matching_meta
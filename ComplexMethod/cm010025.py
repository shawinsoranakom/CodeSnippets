def _get_allowed_globals():
    rc: dict[str, Any] = {
        "collections.OrderedDict": OrderedDict,
        "collections.Counter": Counter,
        "torch.nn.parameter.Parameter": torch.nn.Parameter,
        "torch.serialization._get_layout": torch.serialization._get_layout,
        "torch.Size": torch.Size,
        "torch.Tensor": torch.Tensor,
        "torch.device": torch.device,
        "_codecs.encode": encode,  # for bytes
        "builtins.bytearray": bytearray,  # for bytearray
        "builtins.set": set,  # for set
        "builtins.complex": complex,  # for complex
    }

    # dtype
    for t in torch.storage._dtype_to_storage_type_map():
        rc[str(t)] = t
    for t in torch.storage._new_dtypes():
        rc[str(t)] = t
    for t in [getattr(torch, f"uint{x}") for x in range(1, 8)]:
        rc[str(t)] = t
    for t in [getattr(torch, f"int{x}") for x in range(1, 8)]:
        rc[str(t)] = t

    # Tensor classes
    for tt in torch._tensor_classes:
        rc[f"{tt.__module__}.{tt.__name__}"] = tt
    # Storage classes
    for ts in torch._storage_classes:
        if ts not in (torch.storage.TypedStorage, torch.storage.UntypedStorage):
            # Wrap legacy storage types in a dummy class
            rc[f"{ts.__module__}.{ts.__name__}"] = torch.serialization.StorageType(
                ts.__name__
            )
        else:
            rc[f"{ts.__module__}.{ts.__name__}"] = ts
    # Quantization specific
    for qt in [
        torch.per_tensor_affine,
        torch.per_tensor_symmetric,
        torch.per_channel_affine,
        torch.per_channel_symmetric,
        torch.per_channel_affine_float_qparams,
    ]:
        rc[str(qt)] = qt
    # Rebuild functions
    for f in _tensor_rebuild_functions():
        rc[f"torch._utils.{f.__name__}"] = f

    # Handles Tensor Subclasses, Tensor's with attributes.
    # NOTE: It calls into above rebuild functions for regular Tensor types.
    rc["torch._tensor._rebuild_from_type_v2"] = torch._tensor._rebuild_from_type_v2
    return rc
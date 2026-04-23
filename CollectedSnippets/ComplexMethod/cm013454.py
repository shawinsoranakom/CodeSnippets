def extract_val(val: _ExtractValType, include_real: bool = False) -> _ExtractValType:
    if is_fake(val):
        return snapshot_fake(val, include_real=include_real)
    elif isinstance(val, py_sym_types):
        return val
    elif isinstance(val, (_AnyScriptObject, OpaqueBase)):
        return val
    elif isinstance(val, BackwardState):
        return val
    elif is_opaque_value(val):
        return val
    elif isinstance(val, (list, tuple)):
        return val.__class__([extract_val(x) for x in val])
    elif isinstance(val, dict):
        return {k: extract_val(v) for k, v in val.items()}
    elif isinstance(val, Tensor):
        if not val.is_sparse:
            # NB: Kinda hacky, but we should try to get val as the metadata
            # everywhere
            # TODO: This doesn't properly track storages.  A more robust
            # approach would be to maintain a per-trace FakeTensorMode and
            # from_real_tensor to create fake values (don't forget to
            # snapshot_fake)
            from torch._guards import detect_fake_mode

            fake_tensor_mode = detect_fake_mode(val)
            if not fake_tensor_mode:
                fake_tensor_mode = FakeTensorMode(allow_fallback_kernels=True)
            with fake_tensor_mode:
                return torch.empty_strided(
                    val.shape, val.stride(), device=val.device, dtype=val.dtype
                )
        else:
            return None
    elif isinstance(val, (int, float, bool)):
        return val
    elif val is None:
        return None

    typing_extensions.assert_never(val)
def _attach_bnb_multidevice_hooks(
    model, load_in_4bit, load_in_8bit, offload_embedding, fast_inference
):
    """
    Attach accelerate AlignDevicesHook on a bnb model loaded across multiple
    devices (or a non-default device).  No-op for single-GPU cuda:0, non-bnb,
    vLLM, or already-dispatched models.
    """
    if fast_inference:
        return
    is_bnb = (
        load_in_4bit
        or load_in_8bit
        or getattr(model, "is_loaded_in_4bit", False)
        or getattr(model, "is_loaded_in_8bit", False)
        or getattr(model, "quantization_method", None) == "bitsandbytes"
    )
    if not is_bnb:
        return
    if offload_embedding:
        return
    if getattr(model, "hf_device_map", None) is not None:
        return  # already dispatched

    try:
        all_devs = {p.device for p in model.parameters()}
    except Exception as exc:
        warnings.warn(
            "Unsloth: Failed to determine device placement from model parameters, "
            f"so multi-GPU hooks cannot be attached. ({type(exc).__name__}: {exc})",
            RuntimeWarning,
            stacklevel = 2,
        )
        return

    cuda_devs = {d for d in all_devs if d.type == "cuda"}
    if not cuda_devs:
        return

    default_cuda = torch.device("cuda", 0)
    if all_devs == {default_cuda}:
        return

    try:
        from accelerate import dispatch_model
    except ImportError:
        return  # accelerate not available

    try:
        inferred_map = _infer_device_map_from_loaded_model(model)
        if not inferred_map:
            return

        # bnb constructors reject _is_hf_initialized; strip before dispatch.
        _extra_keys = ("_is_hf_initialized",)
        _stripped = []
        for _, param in model.named_parameters():
            for key in _extra_keys:
                if key in param.__dict__:
                    _stripped.append((param, key, param.__dict__.pop(key)))

        try:
            # CUDA -> int index, non-CUDA -> type string ("cpu", "meta").
            device_map_int = {
                k: (v.index if v.type == "cuda" else v.type)
                if isinstance(v, torch.device)
                else v
                for k, v in inferred_map.items()
            }

            # force_hooks=True: install hooks even for single-device maps.
            main_device = device_map_int.get("")
            if main_device in (None, "cpu", "disk"):
                main_device = next(
                    (d for d in device_map_int.values() if d not in ("cpu", "disk")),
                    None,
                )
            dispatch_model(
                model,
                device_map = device_map_int,
                main_device = main_device,
                skip_keys = getattr(model, "_skip_keys_device_placement", None),
                force_hooks = True,
            )
            desc = f"{len(inferred_map)} block(s) across {len(cuda_devs)} device(s)"
        finally:
            # Restore stripped keys.
            for param, key, val in _stripped:
                param.__dict__[key] = val

        logger.info(
            f"Unsloth: Attached accelerate AlignDevicesHook ({desc}) "
            f"for bnb multi-GPU inference."
        )
    except Exception as exc:
        warnings.warn(
            f"Unsloth: Could not attach multi-device dispatch hooks automatically "
            f"({type(exc).__name__}: {exc}). "
            "Cross-device inference may fail. Consider using a single GPU or "
            "calling accelerate.dispatch_model() manually.",
            RuntimeWarning,
            stacklevel = 2,
        )
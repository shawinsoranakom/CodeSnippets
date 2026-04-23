def fix_trl_vllm_ascend():
    # transformers >= 4.48's `_is_package_available(name)` returns a tuple
    # (bool, version_or_None). TRL caches that tuple in module-level
    # `_*_available` flags and the matching `is_*_available()` accessors
    # return the tuple directly. A non-empty tuple is always truthy, so
    # `if is_X_available():` fires even when X is absent, triggering an
    # unconditional `import X` that fails. The surfaced case is
    # `vllm_ascend` (blocks `from trl import GRPOConfig, GRPOTrainer`
    # outside Huawei Ascend hosts); `llm_blender`, `deepspeed`, `joblib`
    # share the same shape. Coerce every tuple-cached flag in
    # trl.import_utils to bool; the existing accessors that just return
    # the cached value then naturally yield a bool.
    if importlib.util.find_spec("trl") is None:
        return
    try:
        import trl.import_utils as tiu
    except Exception:
        return
    for attr in list(vars(tiu)):
        if not (attr.startswith("_") and attr.endswith("_available")):
            continue
        cached = getattr(tiu, attr)
        if isinstance(cached, tuple):
            setattr(tiu, attr, bool(cached and cached[0]))
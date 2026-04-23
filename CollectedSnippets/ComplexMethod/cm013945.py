def _validate_backend_names(config_str: str) -> str | None:
    """Return an error message if any backend name is invalid, else None."""
    if not config_str or not config_str.strip():
        return None
    from .backends.registry import lookup_backend

    for rule_str in config_str.split(";"):
        rule_str = rule_str.strip()
        if not rule_str or ":" not in rule_str:
            continue
        backend_name = rule_str[rule_str.find(":") + 1 :].strip()
        if not backend_name:
            continue
        try:
            lookup_backend(backend_name)
        except Exception:
            return (
                f"TORCH_COMPILE_OVERRIDE_BACKENDS: "
                f"'{backend_name}' is not a valid backend, "
                f"see `torch._dynamo.list_backends()` for available backends"
            )
    return None
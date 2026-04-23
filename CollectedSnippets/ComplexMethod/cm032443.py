def _is_malformed_tenant_model_value(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if "#" in text:
        return True
    if "@" in text:
        if text.count("@") != 1:
            return True
        model_name, factory = text.rsplit("@", 1)
        if not model_name or not factory:
            return True
    return False
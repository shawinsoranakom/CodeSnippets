def _normalize_tenant_model_value(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "#" in text:
        text = text.split("#", 1)[0].strip()
    if not text:
        return ""
    if "@" in text:
        if text.count("@") != 1:
            return ""
        model_name, factory = text.rsplit("@", 1)
        if not model_name or not factory:
            return ""
    return text
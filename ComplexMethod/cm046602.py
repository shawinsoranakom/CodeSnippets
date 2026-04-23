def _parse_oxc_validation_marker(fn_name: str) -> tuple[str, str, str]:
    marker = f"{OXC_VALIDATION_FN_MARKER}:"
    if not fn_name.startswith(marker):
        return "javascript", "syntax", "auto"
    suffix = fn_name[len(marker) :]
    parts = [part.strip() for part in suffix.split(":") if part.strip()]
    if len(parts) < 2:
        return "javascript", "syntax", "auto"
    code_lang = parts[0] if parts[0] in _OXC_LANG_TO_NODE_LANG else "javascript"
    mode = parts[1] if parts[1] in _OXC_VALIDATION_MODES else "syntax"
    code_shape = (
        parts[2] if len(parts) >= 3 and parts[2] in _OXC_CODE_SHAPES else "auto"
    )
    return code_lang, mode, code_shape
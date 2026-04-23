def _merge_params(doc_params: list[ParameterDoc], signature_params: list[ParameterDoc]) -> list[ParameterDoc]:
    """Merge docstring params with signature params to include defaults/types."""
    sig_map = {p.name.lstrip("*"): p for p in signature_params}
    merged: list[ParameterDoc] = []

    seen = set()
    for dp in doc_params:
        sig = sig_map.get(dp.name.lstrip("*"))
        merged.append(
            ParameterDoc(
                name=dp.name,
                type=dp.type or (sig.type if sig else None),
                description=dp.description,
                default=sig.default if sig else None,
            )
        )
        seen.add(dp.name.lstrip("*"))

    for name, sig in sig_map.items():
        if name in seen:
            continue
        merged.append(sig)

    return merged
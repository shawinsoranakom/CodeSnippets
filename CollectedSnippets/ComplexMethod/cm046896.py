def _iter_amdgpu_asic_id_table_candidates():
    # Try torch-adjacent ids table paths first without importing torch.
    try:
        torch_spec = importlib.util.find_spec("torch")
    except Exception:
        torch_spec = None

    roots = []
    if torch_spec is not None:
        if torch_spec.origin:
            roots.append(Path(torch_spec.origin).resolve().parent)
        if torch_spec.submodule_search_locations:
            for location in torch_spec.submodule_search_locations:
                roots.append(Path(location).resolve())

    seen = set()
    for root in roots:
        for candidate in (
            root / "share" / "libdrm" / "amdgpu.ids",
            root.parent / "share" / "libdrm" / "amdgpu.ids",
            root.parent.parent / "share" / "libdrm" / "amdgpu.ids",
        ):
            candidate_str = str(candidate)
            if candidate_str in seen:
                continue
            seen.add(candidate_str)
            yield candidate

    for candidate in _AMDGPU_ASIC_ID_CANDIDATE_PATHS:
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        seen.add(candidate_str)
        yield candidate
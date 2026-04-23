def resolve_hip_gpu_stats_name(gpu_stats):
    name = str(getattr(gpu_stats, "name", "") or "").strip()
    name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    normalized_name = name.lower().strip(". ")
    if normalized_name and normalized_name not in ("amd radeon graphics",):
        return name + ". "

    try:
        torch_name = str(torch.cuda.get_device_name(0) or "").strip()
        torch_name = re.sub(r"\s*\([^)]*\)\s*$", "", torch_name).strip()
    except Exception:
        torch_name = ""
    normalized_torch_name = torch_name.lower().strip(". ")
    if normalized_torch_name and normalized_torch_name not in ("amd radeon graphics",):
        return torch_name + ". "

    arch_name = ""
    for key in ("gcnArchName", "gcn_arch_name", "arch_name", "gfx_arch_name"):
        value = getattr(gpu_stats, key, None)
        if value is not None and str(value).strip():
            arch_name = str(value).strip()
            break

    if arch_name:
        arch_name = arch_name.strip()
        match = re.search(r"(gfx[0-9a-z]+)", arch_name, flags = re.I)
        if match:
            return f"AMD {match.group(1).lower()} GPU. "
    return "AMD GPU. "
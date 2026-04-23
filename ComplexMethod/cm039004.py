def _expand_flash_attn_variants(
    all_backends: list[dict[str, Any]],
    fa_features: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expand FLASH_ATTN into FA2, FA3, and FA4 variants."""
    expanded = []
    for backend in all_backends:
        if backend["name"] != "FLASH_ATTN":
            backend.setdefault("_sort_key", backend["name"])
            backend.setdefault("_sort_order", 0)
            backend.setdefault("version", "")
            expanded.append(backend)
            continue

        # Create FA2 entry (keeps base backend's compute_capability)
        fa2 = backend.copy()
        fa2["version"] = "FA2*"
        fa2["_sort_key"] = "FLASH_ATTN"
        fa2["_sort_order"] = 0
        fa2["supports_sink"] = fa_features["fa2"]["supports_sink"]

        # Create FA3 entry (uses parsed compute_capability from fa_utils)
        fa3 = backend.copy()
        fa3["version"] = "FA3*"
        fa3["_sort_key"] = "FLASH_ATTN"
        fa3["_sort_order"] = 1
        if fa_features["fa3"]["compute_capability"]:
            fa3["compute_capability"] = fa_features["fa3"]["compute_capability"]
        fa3["supports_sink"] = fa_features["fa3"]["supports_sink"]
        if fa_features["fa3"]["supports_fp8"]:
            base_dtypes = backend["kv_cache_dtypes"].split(", ")
            fp8_dtypes = ["fp8", "fp8_e4m3", "fp8_e5m2"]
            new_dtypes = [d for d in fp8_dtypes if d not in base_dtypes]
            fa3["kv_cache_dtypes"] = ", ".join(base_dtypes + new_dtypes)

        expanded.append(fa2)
        expanded.append(fa3)

        # Create FA4 entry if FA4 features are available
        if "fa4" in fa_features:
            fa4 = backend.copy()
            fa4["version"] = "FA4*"
            fa4["_sort_key"] = "FLASH_ATTN"
            fa4["_sort_order"] = 2
            if fa_features["fa4"].get("compute_capability"):
                fa4["compute_capability"] = fa_features["fa4"]["compute_capability"]
            fa4["supports_sink"] = fa_features["fa4"]["supports_sink"]
            expanded.append(fa4)

    return expanded
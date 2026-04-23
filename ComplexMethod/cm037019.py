def _build_index() -> dict[str, str]:
    """Walk the vllm package and build a name -> qualified path index."""
    index: dict[str, str] = {}
    # Track conflicts: if multiple modules define the same name,
    # prefer shallower modules (more likely to be the public API).
    depth: dict[str, int] = {}

    for filepath in sorted(VLLM_DIR.rglob("*.py")):
        # Skip internal/private modules
        if any(part.startswith("_") and part != "__init__" for part in filepath.parts):
            continue
        # Skip third-party vendored code
        rel = filepath.relative_to(VLLM_DIR)
        if rel.parts and rel.parts[0] in ("third_party", "vllm_flash_attn"):
            continue

        module_depth = len(filepath.relative_to(ROOT_DIR).parts)
        file_names = _index_file(filepath)

        for name, qualified in file_names.items():
            if name not in index or module_depth < depth[name]:
                index[name] = qualified
                depth[name] = module_depth

    return index
def analyze_backend(backend_name: str, class_path: str) -> dict[str, Any] | None:
    """Analyze a backend class and extract feature information."""
    file_path = get_file_from_class_path(class_path)
    if file_path is None:
        return None

    try:
        tree = ast.parse(file_path.read_text())
    except Exception as e:
        print(f"  Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return None

    class_name = class_path.rsplit(".", 1)[1]
    class_node = find_class_in_ast(tree, class_name)
    if class_node is None:
        return None

    # Check if this is an MLA backend by parent class or naming
    parent = _get_parent_class_name(class_node)
    mla_parents = {"MLACommonBackend", "FlashMLABackend", "FlashMLASparseBackend"}
    is_mla_backend = (
        parent in mla_parents
        or ".mla." in class_path.lower()
        or "_mla" in backend_name.lower()
    )

    # Determine compute capability - use N/A for non-CUDA backends
    is_non_cuda = backend_name.startswith(("CPU_", "ROCM_"))
    compute_cap = "N/A" if is_non_cuda else parse_compute_capability(class_node)

    # Parse impl class features (DCP support)
    impl_method = find_method(class_node, "get_impl_cls")
    impl_class_name = None
    if impl_method:
        for stmt in ast.walk(impl_method):
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Name):
                impl_class_name = stmt.value.id
                break

    supports_dcp = False
    if impl_class_name:
        supports_dcp = parse_impl_bool_attr(
            tree, impl_class_name, "can_return_lse_for_decode", False, file_path
        )

    kv_cache_dtypes = parse_kv_cache_dtypes(class_node)
    if backend_name in BACKEND_KV_DTYPE_EXCLUDES:
        excluded = BACKEND_KV_DTYPE_EXCLUDES[backend_name]
        kv_cache_dtypes = ", ".join(
            d
            for d in (d.strip() for d in kv_cache_dtypes.split(","))
            if d not in excluded
        )

    return {
        "name": backend_name,
        "dtypes": parse_supported_dtypes(class_node),
        "kv_cache_dtypes": kv_cache_dtypes,
        "block_sizes": parse_block_sizes(class_node),
        "head_sizes": parse_head_sizes(class_node),
        "attn_types": parse_attention_types(class_node),
        "compute_capability": compute_cap,
        "is_mla": is_mla_backend or check_method_overrides(class_node, "is_mla"),
        "supports_sink": check_method_overrides(class_node, "supports_sink"),
        "is_sparse": check_method_overrides(class_node, "is_sparse"),
        "supports_mm_prefix": check_method_overrides(class_node, "supports_mm_prefix"),
        "supports_dcp": supports_dcp,
    }
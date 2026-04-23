def _get_backend_config(backend: str) -> dict:
    """
    Get backend configuration from AttentionBackendEnum.

    Uses the registry to get the backend class and extract configuration
    from its methods (get_impl_cls, get_builder_cls, is_sparse, etc.).

    Args:
        backend: Backend name matching AttentionBackendEnum exactly
        (e.g., "FLASHMLA_SPARSE")

    Returns:
        Dict with backend configuration
    """
    from vllm.v1.attention.backend import MultipleOf
    from vllm.v1.attention.backends.registry import AttentionBackendEnum

    try:
        backend_enum = AttentionBackendEnum[backend]
        backend_class = backend_enum.get_class()
    except (KeyError, ValueError) as e:
        valid_backends = [e.name for e in AttentionBackendEnum if e.name != "CUSTOM"]
        raise ValueError(
            f"Unknown backend: {backend}. "
            f"Valid MLA backends: {[b for b in valid_backends if 'MLA' in b]}"
        ) from e

    # Get block size from backend class
    block_sizes = backend_class.get_supported_kernel_block_sizes()
    # Use first supported block size (backends typically support one for MLA)
    block_size = block_sizes[0] if block_sizes else None
    if isinstance(block_size, MultipleOf):
        # No fixed block size; fall back to config value
        block_size = None

    # Check if sparse via class method if available
    is_sparse = getattr(backend_class, "is_sparse", lambda: False)()

    # Get properties that can't be inferred
    props = _BACKEND_PROPERTIES.get(backend, {})

    return {
        "backend_class": backend_class,
        "impl_class": backend_class.get_impl_cls(),
        "builder_class": backend_class.get_builder_cls(),
        "query_format": props.get("query_format", "tuple"),
        "block_size": block_size,
        "is_sparse": is_sparse,
    }
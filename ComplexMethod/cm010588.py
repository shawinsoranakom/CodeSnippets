def blas_workspace_size(
    size: None | int = None,
    backend: None | str | torch._C._BlasBackend = None,
) -> int:
    r"""Query or set the BLAS workspace size for a given backend.

    Convenience wrapper that dispatches to :func:`cublas_workspace_size` or
    :func:`cublaslt_workspace_size` depending on the backend.

    When *backend* is ``None`` the current :func:`preferred_blas_library` is
    used.  ``Default`` is resolved to the platform's default backend (cuBLAS
    on NVIDIA, potentially hipBLASLt on supported ROCm architectures).

    .. note::

       When ``TORCH_CUBLASLT_UNIFIED_WORKSPACE`` is enabled (the default on
       open-source CUDA builds), the cuBLASLt workspace is capped at the
       cuBLAS workspace size and physically reuses the same allocation.
       Setting a large cuBLASLt workspace via this function will therefore
       *not* increase memory beyond the cuBLAS workspace size.

    .. note::

        Setting the workspace size for the cublas backend will take precedence
        over the CUBLAS_WORKSPACE_CONFIG environment variable, and setting the
        workspace size for the cublaslt backend will take precedence over the
        CUBLASLT_WORKSPACE_SIZE environment variable.

    Args:
        size (int, optional): workspace size in bytes.  Must be non-negative.
            When omitted the current size is returned without modification.
        backend (str | torch._C._BlasBackend, optional): which backend's
            workspace to query/set.  Accepts the same strings as
            :func:`preferred_blas_library` (e.g. ``"cublas"``, ``"cublaslt"``).

    Returns:
        int: the current (or newly set) workspace size in bytes.

    Raises:
        RuntimeError: if the resolved backend is CK (no workspace concept).
    """
    if backend is None:
        resolved = preferred_blas_library()
    elif isinstance(backend, str):
        if backend not in _BlasBackends:
            raise RuntimeError(
                f"Unknown backend string. Choose from: {_BlasBackends_str}."
            )
        resolved = _BlasBackends[backend]
    elif isinstance(backend, torch._C._BlasBackend):
        resolved = backend
    else:
        raise RuntimeError("Unknown backend type.")

    if resolved == torch._C._BlasBackend.Default:
        resolved = torch._C._get_blas_default_backend()

    if resolved == torch._C._BlasBackend.Ck:
        raise RuntimeError("CK backend does not use a workspace.")

    if resolved == torch._C._BlasBackend.Cublaslt:
        return cublaslt_workspace_size(size)
    return cublas_workspace_size(size)
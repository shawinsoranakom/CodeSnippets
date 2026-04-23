def load_and_register_attn_kernel(
    attn_implementation: str, attention_wrapper: Callable | None = None, allow_all_kernels: bool = False
) -> ModuleType | None:
    """
    Load and register the kernel associated to `attn_implementation`.

    Args:
        attn_implementation: A string, usually a kernel repo like "kernels-community/flash-mla".
        attn_wrapper: a callable for the wrapper around the attention implementation. In `transformers` we
            have a wrapper around the `flash_attn_var_len` call, and the same goes for `sdpa` and `eager`.
            They just prepare the arguments properly. This is mostly used for continious batching, where we
            want the `paged` wrapper, which calls the paged cache.
        allow_all_kernels (`bool`, optional):
            Whether to load kernels from unverified hub repos, if it is a custom kernel outside of the `kernels-community`
            hub repository.
    """
    from ..masking_utils import ALL_MASK_ATTENTION_FUNCTIONS
    from ..modeling_utils import ALL_ATTENTION_FUNCTIONS

    actual_attn_name = attn_implementation.split("|")[1] if "|" in attn_implementation else attn_implementation
    if not is_kernel(actual_attn_name):
        return None
    if not _kernels_available:
        raise ImportError(
            "`kernels` is either not installed or uses an incompatible version. "
            "Please install the latest version with `pip install -U kernels`."
        )

    # Extract repo_id and kernel_name from the string
    if ":" in actual_attn_name:
        repo_id, kernel_name = actual_attn_name.split(":")
        kernel_name = kernel_name.strip()
    else:
        repo_id = actual_attn_name
        kernel_name = None
    repo_id = repo_id.strip()
    # extract the rev after the @ if it exists
    repo_id, _, rev = repo_id.partition("@")
    repo_id = repo_id.strip()
    rev = rev.strip() if rev else None

    # Load the kernel from hub
    try:
        kernel = get_kernel(repo_id, revision=rev, allow_all_kernels=allow_all_kernels)
    except Exception as e:
        raise ValueError(f"An error occurred while trying to load from '{repo_id}': {e}.")
    # correctly wrap the kernel
    if hasattr(kernel, "flash_attn_varlen_func"):
        if attention_wrapper is None:
            attention_wrapper = flash_attention_forward
        kernel_function = attention_wrapper
    elif kernel_name is not None:
        kernel_function = getattr(kernel, kernel_name)

    # Register the kernel as a valid attention
    ALL_ATTENTION_FUNCTIONS.register(attn_implementation, kernel_function)
    ALL_MASK_ATTENTION_FUNCTIONS.register(attn_implementation, ALL_MASK_ATTENTION_FUNCTIONS["flash_attention_2"])

    return kernel
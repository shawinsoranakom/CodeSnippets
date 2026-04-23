def _lazy_imports(
    implementation: str | None, attention_wrapper: Callable | None = None, allow_all_kernels: bool = False
):
    """
    Lazy loads the respective flash attention implementations.

    Return:
        flash_attn_func: The base flash attention function.
        flash_attn_varlen_func: The flash attention function supporting variable sequence lengths,
                                e.g. for padding-free training.
        pad_input: The function to pad inputs into one sequence and returning the respective kwargs.
        unpad_input: The function to unpad outputs based on the kwargs (from pad_input).
    """
    is_fa2 = is_flash_attn_2_available()
    is_fa3 = is_flash_attn_3_available()
    is_fa4 = is_flash_attn_4_available()

    pad_input, unpad_input = _pad_input, _unpad_input

    is_paged = implementation.startswith("paged|")
    implementation = implementation.split("|")[1] if is_paged else implementation

    if (implementation == "flash_attention_2" and is_fa2) or (
        implementation is None and is_fa2 and not is_fa3 and not is_fa4
    ):
        from flash_attn import flash_attn_func, flash_attn_varlen_func, flash_attn_with_kvcache
        from flash_attn.bert_padding import pad_input, unpad_input
    elif is_torch_npu_available():
        # Package `flash-attn` is unavailable on Ascend NPU, which will cause ImportError
        # Flash-Attention2 related apis for Ascend NPU must be imported from `.integrations.npu_flash_attention` module
        from .integrations.npu_flash_attention import npu_flash_attn_func as flash_attn_func
        from .integrations.npu_flash_attention import npu_flash_attn_varlen_func as flash_attn_varlen_func
        from .integrations.npu_flash_attention import npu_flash_attn_with_kvcache as flash_attn_with_kvcache
    else:
        if implementation == "flash_attention_3" or (implementation is None and is_fa3 and not is_fa4):
            from flash_attn_interface import flash_attn_func, flash_attn_varlen_func, flash_attn_with_kvcache
        elif implementation == "flash_attention_4" or (implementation is None and is_fa4):
            from flash_attn.cute import flash_attn_func, flash_attn_varlen_func

            flash_attn_with_kvcache = None  # not supported yet
        # Kernels fallback
        else:
            from .integrations.hub_kernels import load_and_register_attn_kernel

            # Map standard attention names to hub kernel repos
            kernel_repo = FLASH_ATTN_KERNEL_FALLBACK.get(implementation, implementation)
            # We want to explicitly register the name with `paged|` if found
            kernel_implementation = f"paged|{implementation}" if is_paged else kernel_repo
            kernel = load_and_register_attn_kernel(
                kernel_implementation, attention_wrapper, allow_all_kernels=allow_all_kernels
            )

            flash_attn_func = getattr(kernel, "flash_attn_func", None)
            flash_attn_varlen_func = getattr(kernel, "flash_attn_varlen_func", None)
            flash_attn_with_kvcache = getattr(kernel, "flash_attn_with_kvcache", None)
            if flash_attn_varlen_func is None:
                raise ValueError(
                    f"Could not find the currently requested flash attention implementation at `{implementation}`."
                    "Make sure that you request a valid kernel from the hub, e.g. `kernels-community/flash-attn2`."
                )
            if flash_attn_func is None:
                logger.warning(
                    f"The loaded flash attention implementation at `{implementation}` only supports varlen, i.e. "
                    "it can only be used with continuous batching and does not support the full functionality for "
                    "the base transformers generation methods."
                )
            if flash_attn_with_kvcache is None:
                logger.warning(
                    f"The loaded flash attention implementation at `{implementation}` does not support block tables, so"
                    " the full performances of continuous batching will not be achieved, only the varlen path will be "
                    "used."
                )

    return flash_attn_func, flash_attn_varlen_func, flash_attn_with_kvcache, pad_input, unpad_input
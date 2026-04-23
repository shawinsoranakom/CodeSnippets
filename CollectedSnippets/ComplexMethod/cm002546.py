def sdpa_mask(
    batch_size: int,
    q_length: int,
    kv_length: int,
    q_offset: int = 0,
    kv_offset: int = 0,
    mask_function: Callable = causal_mask_function,
    attention_mask: torch.Tensor | None = None,
    local_size: int | None = None,
    allow_is_causal_skip: bool = True,
    allow_is_bidirectional_skip: bool = False,
    allow_torch_fix: bool = True,
    use_vmap: bool = False,
    device: torch.device | str = "cpu",
    **kwargs,
) -> torch.Tensor | None:
    """
    Create a 4D boolean mask of shape `(batch_size, 1, query_length, kv_length)` where a value of True indicates that
    the element should take part in the attention computation, and False that it should not.
    This function can only be used with torch>=2.5, as the context manager is otherwise not available.

    Args:
        batch_size (`int`):
            The batch size of the input sequence.
        q_length (`int`):
            The size that the query states will have during the attention computation.
        kv_length (`int`):
            The size that the key and value states will have during the attention computation.
        kv_offset (`int`, optional):
            An optional offset to indicate at which first position the key and values states will refer to.
        q_offset (`int`, optional):
            An optional offset to indicate at which first position the query states will refer to.
        mask_function (`Callable`):
            The mask factory function describing the mask pattern.
        attention_mask (`torch.Tensor`, optional):
            The 2D attention mask corresponding to padded tokens of shape (batch_size, number_of_seen_tokens+q_length)
        local_size (`int`, optional):
            The size of the local attention, if we do not use full attention. This is used only if `allow_is_causal_skip=True`
            to try to skip mask creation if possible.
        allow_is_causal_skip (`bool`, optional):
            Whether to allow to return `None` for the mask under conditions where we can use the `is_causal` argument in
            `torch.sdpa` instead. Default to `True`.
        allow_is_bidirectional_skip (`bool`, optional):
            Whether to allow to return `None` for the mask under conditions where we do not have to add any bias,
            i.e. full attention without any padding. Default to `False`.
        allow_torch_fix (`bool`, optional):
            Whether to update the mask in case a query is not attending to any tokens, to solve a bug in torch's older
            versions. We need an arg to skip it when using eager. By default `True`.
        use_vmap (`bool`, optional):
            Whether to use `vmap` during the mask construction or not. Allows powerful custom patterns that may not be
            index-based (for the cost of speed performance). By default `False`.
        device (`torch.device` or `str`, optional):
            An optional device to create the mask on.


    ## Creating a simple causal mask:

    To create the following causal mask:

        0 ■ ⬚ ⬚ ⬚ ⬚
        1 ■ ■ ⬚ ⬚ ⬚
        2 ■ ■ ■ ⬚ ⬚
        3 ■ ■ ■ ■ ⬚
        4 ■ ■ ■ ■ ■

    You can do

    ```python
    >>> sdpa_mask(batch_size=1, q_length=5, kv_length=5)
    >>> tensor([[[[ True, False, False, False, False],
                  [ True,  True, False, False, False],
                  [ True,  True,  True, False, False],
                  [ True,  True,  True,  True, False],
                  [ True,  True,  True,  True,  True]]]])
    ```

    ## Creating a sliding window mask:

    To create the following sliding window mask (`sliding_window=3`):

        0 ■ ⬚ ⬚ ⬚ ⬚
        1 ■ ■ ⬚ ⬚ ⬚
        2 ■ ■ ■ ⬚ ⬚
        3 ⬚ ■ ■ ■ ⬚
        4 ⬚ ⬚ ■ ■ ■

    You can do

    ```python
    >>> sdpa_mask(batch_size=1, q_length=5, kv_length=5, mask_function=sliding_window_causal_mask_function(3))
    >>> tensor([[[[ True, False, False, False, False],
                  [ True,  True, False, False, False],
                  [ True,  True,  True, False, False],
                  [False,  True,  True,  True, False],
                  [False, False,  True,  True,  True]]]])
    ```

    ## Creating a chunked attention mask

    To create the following chunked attention mask (`chunk_size=3`):

        0 ■ ⬚ ⬚ ⬚ ⬚
        1 ■ ■ ⬚ ⬚ ⬚
        2 ■ ■ ■ ⬚ ⬚
        3 ⬚ ⬚ ⬚ ■ ⬚
        4 ⬚ ⬚ ⬚ ■ ■

    You can do

    ```python
    >>> sdpa_mask(batch_size=1, q_length=5, kv_length=5, mask_function=chunked_causal_mask_function(3, torch.zeros(1, dtype=int)))
    >>> tensor([[[[ True, False, False, False, False],
                [ True,  True, False, False, False],
                [ True,  True,  True, False, False],
                [False, False, False,  True, False],
                [False, False, False,  True,  True]]]])
    ```

    """
    # For BC on `cache_positions` that used to be an arg at the position of `q_length`
    if isinstance(q_length, torch.Tensor):
        logger.warning_once(
            "`cache_position` is deprecated as an arg, and will be removed in Transformers v5.6. Please use `q_length` and "
            "`q_offset` instead, similarly to `kv_length` and `kv_offset`"
        )
        q_length, q_offset = q_length.shape[0], q_length[0].to(device)

    # Potentially pad the 2D mask
    padding_mask = prepare_padding_mask(attention_mask, kv_length, kv_offset)

    # Under specific conditions, we can avoid materializing the mask
    #   1. Causal masks can rely on the `is_causal` argument
    #   2. Bidirectional do not need any further processing (no bias)
    if allow_is_causal_skip and _ignore_causal_mask_sdpa(padding_mask, q_length, kv_length, kv_offset, local_size):
        return None
    if allow_is_bidirectional_skip and _ignore_bidirectional_mask_sdpa(padding_mask, kv_length, local_size):
        return None

    # Potentially add the padding 2D mask
    if padding_mask is not None:
        mask_function = and_masks(mask_function, padding_mask_function(padding_mask))

    batch_arange = torch.arange(batch_size, device=device)
    head_arange = torch.arange(1, device=device)
    q_arange = torch.arange(q_length, device=device) + q_offset
    kv_arange = torch.arange(kv_length, device=device) + kv_offset

    # Actual mask creation
    # Option 1: Fast non-vmap mask creation (default)
    if not use_vmap:
        # Apply mask function element-wise through broadcasting
        attention_mask = mask_function(*_non_vmap_expansion_sdpa(batch_arange, head_arange, q_arange, kv_arange))
        # Expand the mask to match batch size and query length if they weren't used in the mask function
        attention_mask = attention_mask.expand(batch_size, -1, q_length, kv_length)

    # Option 2: Vmap mask creation (torch>=2.6 and custom patterns)
    elif _is_torch_greater_or_equal_than_2_6:
        # This creates the 4D mask easily. Note that we need this context manager as vmap cannot handle slicing a tensor from
        # scalar tensor (it internally calls `.item()` which vmap does not allow, but this context works around it
        # We don't need to add an offset to the mask_function either, as we vmap directly the correct indices for k and kv indices
        with TransformGetItemToIndex():
            attention_mask = _vmap_expansion_sdpa(mask_function)(batch_arange, head_arange, q_arange, kv_arange)

    # Option 3: Error out since it indicates that the user did something custom, which they shouldn't have (torch<2.6)
    else:
        raise ValueError(
            "The vmap functionality for mask creation is only supported from torch>=2.6. "
            "Please update your torch version or use `use_vmap=False` with index-based masks."
        )

    # Due to a bug in versions of torch<2.5, we need to update the mask in case a query is not attending to any
    # tokens (due to padding). See details in https://github.com/pytorch/pytorch/issues/110213
    if not _is_torch_greater_or_equal_than_2_5 and allow_torch_fix:
        attention_mask = attention_mask | torch.all(~attention_mask, dim=-1, keepdim=True)

    return attention_mask
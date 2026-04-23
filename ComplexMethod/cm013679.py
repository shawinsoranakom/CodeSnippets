def create_block_mask(
    mask_mod: _mask_mod_signature,
    B: int | None,
    H: int | None,
    Q_LEN: int,
    KV_LEN: int,
    device: DeviceLikeType | None = None,
    BLOCK_SIZE: int | tuple[int, int] = _DEFAULT_SPARSE_BLOCK_SIZE,
    _compile=False,
) -> BlockMask:
    r"""This function creates a block mask tuple from a mask_mod function.

    Args:
        mask_mod (Callable): mask_mod function. This is a callable that defines the
            masking pattern for the attention mechanism. It takes four arguments:
            b (batch size), h (number of heads), q_idx (query index), and kv_idx (key/value index).
            It should return a boolean tensor indicating which attention connections are allowed (True)
            or masked out (False).
        B (int): Batch size.
        H (int): Number of query heads.
        Q_LEN (int): Sequence length of query.
        KV_LEN (int): Sequence length of key/value.
        device (str): Device to run the mask creation on.
        BLOCK_SIZE (int or tuple[int, int]): Block size for the block mask. If a single int is provided it is used for both query and key/value.

    Returns:
        BlockMask:  A BlockMask object that contains the block mask information.

    Example Usage:
        .. code-block:: python

            def causal_mask(b, h, q_idx, kv_idx):
                return q_idx >= kv_idx


            block_mask = create_block_mask(causal_mask, 1, 1, 8192, 8192, device="cuda")
            query = torch.randn(1, 1, 8192, 64, device="cuda", dtype=torch.float16)
            key = torch.randn(1, 1, 8192, 64, device="cuda", dtype=torch.float16)
            value = torch.randn(1, 1, 8192, 64, device="cuda", dtype=torch.float16)
            output = flex_attention(query, key, value, block_mask=block_mask)
    """
    if device is None:
        device = torch.accelerator.current_accelerator() or "cpu"
    mod_type = _get_mod_type(mask_mod)
    if mod_type != _ModificationType.MASK_MOD:
        raise AssertionError(
            f"create-block_mask requires a mask_mod function! Got {mask_mod}"
        )
    if B is None:
        B = 1
    if H is None:
        H = 1
    if isinstance(BLOCK_SIZE, int):
        Q_BLOCK_SIZE = BLOCK_SIZE
        KV_BLOCK_SIZE = BLOCK_SIZE
    else:
        Q_BLOCK_SIZE, KV_BLOCK_SIZE = BLOCK_SIZE

    if _compile:
        warnings.warn(
            "_compile flag on create_block_mask was originally added to work around a torch.compile limitation. That limitation has since been addressed. So, to compile create_block_mask, we suggest doing torch.compile(create_block_mask). This still works for now, but will be removed in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        return torch.compile(create_block_mask)(
            mask_mod, B, H, Q_LEN, KV_LEN, device, BLOCK_SIZE
        )

    mask_tensor = create_mask(mask_mod, B, H, Q_LEN, KV_LEN, device)
    partial_block_mask, full_block_mask = _convert_mask_to_block_mask(
        mask_tensor,
        Q_BLOCK_SIZE=Q_BLOCK_SIZE,
        KV_BLOCK_SIZE=KV_BLOCK_SIZE,
        separate_full_blocks=True,
    )
    block_mask = _create_sparse_block_from_block_mask(
        (partial_block_mask, full_block_mask),
        mask_mod,
        (Q_LEN, KV_LEN),
        Q_BLOCK_SIZE,
        KV_BLOCK_SIZE,
    )
    return block_mask
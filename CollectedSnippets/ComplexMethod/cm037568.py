def lightning_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    ed: torch.Tensor,
    block_size: int = 256,
    kv_history: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Apply lightning attention algorithm
    to compute attention efficiently.

    Args:
        q: Query tensor of shape [batch, heads, seq_len, dim]
        k: Key tensor of shape [batch, heads, seq_len, dim]
        v: Value tensor of shape [batch, heads, seq_len, dim_v]
        ed: Decay rate tensor of shape [heads]
        block_size: Size of blocks for block-sparse attention
        kv_history: Optional key-value history from previous computations

    Returns:
        output: Attention output
        kv: Updated key-value history
    """
    d = q.shape[-1]
    e = v.shape[-1]

    if ed.dim() == 1:
        ed = ed.view(1, -1, 1, 1)

    # Split the computation into chunks for better parallelism
    m = 128 if d >= 128 else 64
    assert d % m == 0, f"Dimension d ({d}) must be divisible by m ({m})"
    arr = [m * i for i in range(d // m + 1)]
    if arr[-1] != d:
        arr.append(d)
    n = len(arr)
    output = 0

    # Initialize or clone key-value history
    if kv_history is None:
        kv_history = torch.zeros(
            (q.shape[0], q.shape[1], d, e), dtype=torch.float32, device=q.device
        )
    else:
        kv_history = kv_history.clone().contiguous()

    # Process each chunk and accumulate results
    for i in range(n - 1):
        s = arr[i]
        e = arr[i + 1]
        q1 = q[..., s:e]
        k1 = k[..., s:e]
        o, kv = lightning_attention_(q1, k1, v, ed, kv_history)
        output = output + o
    return output, kv
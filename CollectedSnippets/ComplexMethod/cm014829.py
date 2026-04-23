def rand_sdpa_tensor(shape: SdpaShape, device: str, dtype: torch.dtype, type: str,
                     requires_grad: bool = False, packed: bool = False) -> torch.Tensor:
    """Creates rand dense or nested tensor with given shape and type.

    Args:
        shape (Tuple[int]): Shape of Tensor to construct
        device (str): which device to create tensor on
        dtype (torch.dtype): Tensors' dtype
        type (str): Nested or Dense
        requires_grad (bool, optional): Tensors grad status. Defaults to False.
        packed (bool, optional): Whether to create a single QKV packed or not. Defaults to False.

    Returns:
        torch.Tensor: A new tensor
    """
    batch, num_heads, seq_len, head_dim = shape.batch, shape.num_heads, shape.seq_len, shape.head_dim
    if type == "nested":
        if isinstance(seq_len, list):
            def _size(i):
                return (seq_len[i], num_heads, head_dim) if not packed else (seq_len[i], 3 * num_heads * head_dim)

            return torch.nested.nested_tensor([
                torch.randn(_size(i), device=device, dtype=dtype, requires_grad=requires_grad)
                for i in range(batch)])
        else:
            size = (seq_len, num_heads, head_dim) if not packed else (seq_len, 3 * num_heads * head_dim)
            return torch.nested.nested_tensor([
                torch.randn(size, device=device, dtype=dtype, requires_grad=requires_grad)
                for _ in range(batch)])
    else:
        if not isinstance(seq_len, int):
            raise AssertionError(f"seq_len should be int, got {type(seq_len)}")
        size = (batch, seq_len, num_heads, head_dim) if not packed else (batch, seq_len, 3 * num_heads * head_dim)
        return torch.randn(size, device=device, dtype=dtype, requires_grad=requires_grad)
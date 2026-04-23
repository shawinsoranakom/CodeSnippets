def rotary_embedding_23(
    x: torch.Tensor,
    cos_cache: torch.Tensor,
    sin_cache: torch.Tensor,
    position_ids: torch.Tensor | None = None,
    *,
    interleaved: bool = False,
    num_heads: int = 0,
    rotary_embedding_dim: int = 0,
) -> torch.Tensor:
    """RotaryEmbedding-23 https://onnx.ai/onnx/operators/onnx__RotaryEmbedding.html#rotaryembedding-23"""
    # x has shape (batch_size, num_heads, sequence_length, head_size)
    # or (batch_size, sequence_length, hidden_size)
    input_shape = x.shape
    input_rank = len(input_shape)
    batch_size = input_shape[0]
    sequence_length = input_shape[-2]

    # Validate position_ids and caches match x
    if position_ids is not None:
        torch._check(
            position_ids.dim() == 2,
            lambda: f"position_ids must be 2D when provided. Received shape {position_ids.shape}",
        )
        torch._check(
            position_ids.shape[0] == batch_size,
            lambda: f"position_ids first dim (batch) must match x.shape[0] ({batch_size}). Received {position_ids.shape[0]}",
        )
        torch._check(
            position_ids.shape[1] == sequence_length,
            lambda: f"position_ids second dim (sequence) must match x.shape[-2] ({sequence_length}). Received {position_ids.shape[1]}",
        )
        torch._check(
            cos_cache.dim() == 2 and sin_cache.dim() == 2,
            lambda: "cos_cache/sin_cache must be 2D when position_ids is provided. "
            f"Received cos_cache shape {cos_cache.shape}, sin_cache shape {sin_cache.shape}",
        )
    else:
        torch._check(
            cos_cache.dim() == 3 and sin_cache.dim() == 3,
            lambda: "cos_cache/sin_cache must be 3D when position_ids is not provided. "
            f"Received cos_cache shape {cos_cache.shape}, sin_cache shape {sin_cache.shape}",
        )

    # First ensure x has shape [batch_size, num_heads, seq_len, head_size]
    # So that the rotation logic can be shared with reshaped 3D inputs
    if input_rank == 4:
        # Reshape from (batch_size, num_heads, seq_len, head_size)
        # to [batch_size, seq_len, num_heads, head_size]
        x = torch.permute(x, (0, 2, 1, 3))
    elif input_rank == 3:
        torch._check(
            num_heads != 0,
            lambda: f"num_heads must be provided for 3D inputs. Received input tensor with shape {input_shape}",
        )
        hidden_size = input_shape[2]
        head_size = hidden_size // num_heads
        new_shape = [batch_size, sequence_length, num_heads, head_size]
        x = torch.reshape(x, new_shape)

    torch._check(len(x.shape) == 4, lambda: "x should be a 4D tensor by now")
    head_size = x.shape[3]

    # Fully or partially perform rotation on x based on rotary_embedding_dim attribute
    if rotary_embedding_dim == 0:
        # If rotary_embedding_dim not provided, perform full rotation by using head_size
        rotary_embedding_dim = head_size
    x_rotate = x[:, :, :, :rotary_embedding_dim]
    x_not_rotate = x[:, :, :, rotary_embedding_dim:]
    rotary_embedding_dim_half = rotary_embedding_dim // 2

    # Retrieve sin and cos caches using position ids
    if position_ids is not None:
        cos = cos_cache[
            position_ids
        ]  # Shape: [batch_size, sequence_length, head_size/2]
        sin = sin_cache[
            position_ids
        ]  # Shape: [batch_size, sequence_length, head_size/2]
    else:
        cos = cos_cache  # Shape: [batch_size, sequence_length, rotary_embedding_dim/2]
        sin = sin_cache  # Shape: [batch_size, sequence_length, rotary_embedding_dim/2]

    torch._check(
        cos.shape[0] == batch_size and cos.shape[1] == sequence_length,
        lambda: f"cos has shape {cos.shape} but expected (batch={batch_size}, seq={sequence_length}, ...)",
    )
    torch._check(
        sin.shape[0] == batch_size and sin.shape[1] == sequence_length,
        lambda: f"sin has shape {sin.shape} but expected (batch={batch_size}, seq={sequence_length}, ...)",
    )
    torch._check(
        cos.shape[-1] == rotary_embedding_dim_half,
        lambda: f"Last dimension of cos cache ({cos.shape[-1]}) should match rotary_embedding_dim/2 ({rotary_embedding_dim_half}).",
    )
    torch._check(
        sin.shape[-1] == rotary_embedding_dim_half,
        lambda: f"Last dimension of sin cache ({sin.shape[-1]}) should match rotary_embedding_dim/2 ({rotary_embedding_dim_half}).",
    )
    cos = torch.unsqueeze(
        cos, 2
    )  # Shape: [batch_size, sequence_length, 1, rotary_embedding_dim/2]
    sin = torch.unsqueeze(
        sin, 2
    )  # Shape: [batch_size, sequence_length, 1, rotary_embedding_dim/2]

    # Either divide the x in halves or interleave (based on interleaved attribute)
    if interleaved:
        x1 = x_rotate[:, :, :, 0::2]
        x2 = x_rotate[:, :, :, 1::2]
    else:
        x1, x2 = torch.chunk(x_rotate, 2, dim=-1)

    # Calculate real and imaginary values
    real = cos * x1 - sin * x2
    imag = sin * x1 + cos * x2

    # Inserted rotated embeddings back to the original x
    if interleaved:
        # x_rotate[:, :, :, 0::2] = real
        # x_rotate[:, :, :, 1::2] = imag
        real = torch.unsqueeze(real, -1)
        imag = torch.unsqueeze(imag, -1)
        x_rotate_concat = torch.cat((real, imag), dim=-1)
        x_rotate = torch.reshape(x_rotate_concat, x_rotate.shape)
    else:
        x_rotate = torch.cat((real, imag), dim=-1)
    output = torch.cat((x_rotate, x_not_rotate), dim=-1)
    if input_rank == 3:
        return torch.reshape(output, input_shape)

    # Return the dimensions to the original order
    return torch.permute(output, (0, 2, 1, 3))
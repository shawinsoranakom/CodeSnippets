def attention_23(
    Q: torch.Tensor,
    K: torch.Tensor,
    V: torch.Tensor,
    attn_mask: torch.Tensor | None = None,
    past_key: torch.Tensor | None = None,
    past_value: torch.Tensor | None = None,
    *,
    is_causal: bool = False,
    kv_num_heads: int = 0,
    q_num_heads: int = 0,
    qk_matmul_output_mode: int = 0,
    scale: float | None = None,
    softcap: float = 0.0,
    softmax_precision: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Attention-23 https://onnx.ai/onnx/operators/onnx__Attention.html#attention-23"""

    num_head_dim, sequence_dim, head_dim = 1, 2, 3

    # Store original input shape to determine output shape
    input_shape_len = len(Q.shape)
    batch_size = Q.shape[0]

    # Reshape 3D inputs to 4D format
    if len(Q.shape) == 3:
        torch._check(
            q_num_heads != 0 and kv_num_heads != 0,
            lambda: "q_num_heads and kv_num_heads must be provided for 3D inputs",
        )
        q_sequence_length = Q.shape[1]
        Q = _reshape_3d_to_4d(Q, batch_size, q_num_heads)
        K = _reshape_3d_to_4d(K, batch_size, kv_num_heads)
        V = _reshape_3d_to_4d(V, batch_size, kv_num_heads)

    torch._check(
        len(Q.shape) == 4 and len(K.shape) == 4 and len(V.shape) == 4,
        lambda: "Q, K, and V should be 4D tensors by now",
    )

    # Calculate scale factor if not provided
    q_head_size = Q.shape[head_dim]
    scale = _get_scale_factor(scale, q_head_size)

    # Handle past key/value caches
    present_key = (
        torch.cat([past_key, K], dim=sequence_dim)
        if past_key is not None
        else K.clone()
    )
    present_value = (
        torch.cat([past_value, V], dim=sequence_dim)
        if past_value is not None
        else V.clone()
    )

    # Update K and V to include past states
    K, V = present_key, present_value

    # Get current dimensions
    current_q_num_heads = Q.shape[num_head_dim]
    current_kv_num_heads = K.shape[num_head_dim]
    q_sequence_length = Q.shape[sequence_dim]
    kv_sequence_length = K.shape[sequence_dim]

    # Check if we can use the optimized scaled_dot_product_attention (most optimized)
    can_use_sdpa = (
        softcap == 0.0  # No softcap
        and qk_matmul_output_mode == 0  # Default QK output mode
        and softmax_precision is None  # No custom softmax precision
        and (attn_mask is None or attn_mask.dtype == torch.bool)
    )

    _validate_gqa_configuration(current_q_num_heads, current_kv_num_heads)

    if can_use_sdpa:
        # Use PyTorch's optimized scaled_dot_product_attention
        output = torch.nn.functional.scaled_dot_product_attention(
            Q,
            K,
            V,
            attn_mask=attn_mask,
            dropout_p=0.0,
            is_causal=is_causal,
            scale=scale,
            enable_gqa=bool(
                current_q_num_heads != current_kv_num_heads
            ),  # Ensure enable_gqa is not SymBool
        )

        qk_output = _get_qk_output_for_aten_spda(
            Q,
            K,
            current_q_num_heads,
            current_kv_num_heads,
            scale,
            qk_matmul_output_mode,
        )
    else:
        # Fallback to manual implementation for complex cases

        # Handle Group Query Attention (GQA) and Multi-Query Attention (MQA)
        if current_q_num_heads != current_kv_num_heads:
            repeat_factor = current_q_num_heads // current_kv_num_heads
            K = K.repeat_interleave(repeat_factor, dim=num_head_dim)
            V = V.repeat_interleave(repeat_factor, dim=num_head_dim)

        # Create attention bias
        attn_bias = torch.zeros(
            q_sequence_length, kv_sequence_length, dtype=Q.dtype, device=Q.device
        )

        # Apply causal masking
        if is_causal:
            torch._check(
                attn_mask is None, lambda: "Cannot use both is_causal and attn_mask"
            )
            causal_mask = torch.tril(
                torch.ones(
                    q_sequence_length,
                    kv_sequence_length,
                    dtype=torch.bool,
                    device=Q.device,
                )
            )
            attn_bias = attn_bias.masked_fill(~causal_mask, float("-inf"))

        # Apply attention mask
        if attn_mask is not None:
            if attn_mask.dtype == torch.bool:
                # Boolean mask: True means participate in attention
                attn_bias = attn_bias.masked_fill(~attn_mask, float("-inf"))
            else:
                # Float mask: added to attention scores
                attn_bias = attn_bias + attn_mask

        # Apply scaling factor
        scale_factor = _get_scale_factor(scale, Q.shape[3])

        # Scale both Q and K by sqrt(scale_factor) for numerical stability
        sqrt_scale = math.sqrt(scale_factor)
        Q_scaled = Q * sqrt_scale
        K_scaled = K * sqrt_scale

        # Compute Q @ K^T
        qk_matmul_output = torch.matmul(Q_scaled, K_scaled.transpose(-2, -1))

        # Initialize QK output based on mode
        qk_output = qk_matmul_output  # Default case for mode 0

        # Add attention bias
        qk_with_bias = qk_matmul_output + attn_bias

        if qk_matmul_output_mode == 1:
            qk_output = qk_with_bias

        # Apply softcap if provided
        if softcap > 0.0:
            qk_with_bias = softcap * torch.tanh(qk_with_bias / softcap)

        if qk_matmul_output_mode == 2:
            qk_output = qk_with_bias

        # Apply softmax with optional precision casting
        if softmax_precision is not None:
            # Map ONNX data type to torch dtype
            if softmax_precision in _ATTENTION_23_ALLOWED_INTERMEDIATE_PRECISIONS:
                original_dtype = qk_with_bias.dtype
                qk_with_bias = qk_with_bias.to(
                    _dtype_mappings.ONNX_DTYPE_TO_TORCH_DTYPE[softmax_precision]
                )
                qk_softmax = torch.softmax(qk_with_bias, dim=-1)
                qk_softmax = qk_softmax.to(original_dtype)
            else:
                qk_softmax = torch.softmax(qk_with_bias, dim=-1)
        else:
            qk_softmax = torch.softmax(qk_with_bias, dim=-1)

        if qk_matmul_output_mode == 3:
            qk_output = qk_softmax

        # Compute attention output
        output = torch.matmul(qk_softmax, V)

    # Reshape output back to 3D if input was 3D
    if input_shape_len == 3:
        # output: (batch_size, q_num_heads, q_sequence_length, v_head_size) -> (batch_size, q_sequence_length, hidden_size)
        output = (
            output.transpose(1, 2).contiguous().view(batch_size, q_sequence_length, -1)
        )

    return output, present_key, present_value, qk_output
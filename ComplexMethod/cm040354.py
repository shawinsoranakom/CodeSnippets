def dot_product_attention(
    query,
    key,
    value,
    bias=None,
    mask=None,
    scale=None,
    is_causal=False,
    flash_attention=None,
    attn_logits_soft_cap=None,
):
    """Computes dot-product attention given query, key, and value.

    This is the core computation of attention that is used in transformers.
    For TPU platforms, flash attention optimizations are automatically applied
    when possible, and sharding parameters are inferred from the layout map
    in the current distribution context.

    Args:
        query: Queries with shape `[batch, time, heads,
            depth_k]`.
        key: Keys with shape `[batch, time, heads,
            depth_k]`.
        value: Values with shape `[batch, time, heads,
            depth_v]`.
        bias: Optional bias with shape broadcastable to
            `[batch, heads, dest_time, source_time]`.
        mask: Optional mask with shape broadcastable to
            `[batch, heads, dest_time, source_time]`.
        scale: Float. Optional scale that is applied to the attention
            computation.
        is_causal: Boolean. Specifying whether causal masking is applied.
        flash_attention: Boolean. Whether to use flash attention optimization
            for increased performance. Default to None, which means it will
            be auto-determined based on the platform, input shapes and
            compatibility.
        attn_logits_soft_cap: Float. Optional float to softly cap attention
            logits to avoid numerical stability issues. Applied as:
            `logits = logits / (1.0 + abs(logits) / attn_logits_soft_cap)`.

    Returns:
        JAX Array of shape `[batch, time, heads, depth_v]`.
    """
    query = convert_to_tensor(query)
    key = convert_to_tensor(key)
    value = convert_to_tensor(value)
    if len(query.shape) != 4 or len(key.shape) != 4 or len(value.shape) != 4:
        raise ValueError(
            "`dot_product_attention` only supports 4D inputs. "
            f"Received: query.shape={query.shape}, key.shape={key.shape}, "
            f"value.shape={value.shape}."
        )
    compute_dtype = backend.result_type(query.dtype, key.dtype, value.dtype)
    query = cast(query, compute_dtype)
    key = cast(key, compute_dtype)
    value = cast(value, compute_dtype)
    if bias is not None:
        bias = convert_to_tensor(bias, dtype=compute_dtype)

    # Check platform
    platform = jax.devices()[0].platform
    is_tpu = platform == "tpu"

    # Determine flash attention compatibility
    if flash_attention is None:
        flash_attention = _can_use_flash_attention(query, key, value, bias)
    elif flash_attention is True:
        # Use `raise_error=True` to provide more details if the inputs failed to
        # use flash attention
        _can_use_flash_attention(query, key, value, bias, raise_error=True)

    # TPU-specific flash attention path
    if is_tpu and flash_attention:
        # Get sharding parameters from distribution context
        head_shards = 1
        # Typically keep q_seq_shards=1 for best performance
        q_seq_shards = 1
        try:
            from keras.src.distribution.distribution_lib import ModelParallel
            from keras.src.distribution.distribution_lib import (
                distribution as get_dist,
            )

            # Get current distribution if available
            dist = get_dist()
            if dist and isinstance(dist, ModelParallel):
                mesh = dist.device_mesh
                if "model" in mesh.axis_names:
                    model_dim_index = mesh.axis_names.index("model")
                    # Set head_shards based on the model dimension of the mesh
                    head_shards = mesh.shape[model_dim_index]
        except (ImportError, ValueError, AttributeError):
            # Use default values if detection fails
            logging.exception(
                "Failed to determine distribution context for sharding. "
                "Using default head_shards=1 and q_seq_shards=1."
            )
        # Transpose to ('batch', 'heads', 'length', 'head_dim')
        query_tpu_layout = jnp.transpose(query, axes=(0, 2, 1, 3))
        key_tpu_layout = jnp.transpose(key, axes=(0, 2, 1, 3))
        value_tpu_layout = jnp.transpose(value, axes=(0, 2, 1, 3))

        bs, num_heads, q_len, head_dim = query_tpu_layout.shape

        # Apply scale to query if provided
        if scale is not None:
            # TPU kernel applies 1/sqrt(head_dim) internally, to achieve
            # overall QK^T * scale, scale query by (scale * sqrt(head_dim))
            query_tpu_layout = query_tpu_layout * (scale * math.sqrt(head_dim))

        # Create segment IDs for Splash Attention (for packing/batching)
        segment_ids = jnp.zeros([bs, q_len], dtype=jnp.int32)
        decoder_segment_ids = splash_attention_kernel.SegmentIds(
            q=segment_ids, kv=segment_ids
        )

        # Process mask for Splash Attention
        custom_mask = None
        if mask is not None:
            mask_bool = mask.astype("bool") if mask.dtype != jnp.bool_ else mask

            if mask_bool.ndim == 3 and mask_bool.shape[0] == bs:
                custom_mask = mask_bool[0]
            elif mask_bool.ndim == 4 and mask_bool.shape[0] == bs:
                custom_mask = mask_bool[0, 0]

            if is_causal and custom_mask is not None:
                causal_mask = jnp.tril(
                    jnp.ones((q_len, q_len), dtype=jnp.bool_)
                )
                custom_mask = jnp.logical_and(custom_mask, causal_mask)

        if custom_mask is None and is_causal:
            custom_mask = jnp.tril(jnp.ones((q_len, q_len), dtype=jnp.bool_))

        # Splash attention kernel requires concrete mask values for hashing.
        # If the mask is a tracer (e.g. inside a scan/loop), we must fall back.
        if isinstance(mask, jax.core.Tracer) or isinstance(
            custom_mask, jax.core.Tracer
        ):
            flash_attention = False
        else:
            try:
                output = wrap_flash_attention(
                    query_tpu_layout,
                    key_tpu_layout,
                    value_tpu_layout,
                    decoder_segment_ids=decoder_segment_ids,
                    custom_mask=custom_mask,
                    attn_logits_soft_cap=attn_logits_soft_cap,
                    head_shards=head_shards,
                    q_seq_shards=q_seq_shards,
                )
                # Transpose output back to Keras layout
                return jnp.transpose(output, axes=(0, 2, 1, 3))
            except Exception:
                logging.exception(
                    "Failed to apply Splash kernel for flash attention. "
                    "Falling back to JAX native dot_product_attention."
                )
                flash_attention = False

    # JAX native dot_product_attention for GPU or fallback for TPU
    if hasattr(jax.nn, "dot_product_attention"):
        impls = ["cudnn", "xla"] if flash_attention else ["xla"]
        for impl in impls:
            try:
                return jax.nn.dot_product_attention(
                    query,
                    key,
                    value,
                    bias=bias,
                    mask=mask,
                    scale=scale,
                    is_causal=is_causal,
                    implementation=impl,
                )
            except Exception:
                logging.exception(
                    f"Failed to apply {impl} implementation of "
                    "jax.nn.dot_product_attention."
                )

    if flash_attention:
        raise RuntimeError(
            "Flash attention is not supported in your current JAX version. "
            "Please update it by following the official guide: "
            "https://jax.readthedocs.io/en/latest/installation.html"
        )
    # Ref: jax.nn.dot_product_attention
    # https://github.com/jax-ml/jax/blob/jax-v0.4.33/jax/_src/nn/functions.py#L886
    # Not support `query_seq_lengths` and `key_value_seq_lengths` args

    # Fallback to custom XLA implementation
    # This is the reference implementation from jax.nn.dot_product_attention
    output_shape = query.shape
    _, _, K, H = key.shape
    scale = (1.0 / jnp.sqrt(H)) if scale is None else scale

    # _dot_product_attention_xla
    B, T, N, H = query.shape
    G = N // K
    query = jnp.reshape(query, (B, T, K, G, H))

    def _reshape_to_grouped(t, t_name):
        if t is not None:
            while t.ndim < 4:
                if t.ndim == 3 and t.shape[1] == N:
                    t = jnp.expand_dims(t, axis=2)
                else:
                    t = jnp.expand_dims(t, axis=1)
            tB, tN, tT, tS = t.shape
            if tN == 1:
                t = jnp.broadcast_to(t[:, :, None, :, :], (tB, tN, G, tT, tS))
            else:
                if tN != N:
                    raise ValueError(
                        f"Expected `{t_name}` to have shape (B, 1, T, S) or "
                        f"(B, N, T, S) with N={N} but got {t.shape}."
                    )
                t = jnp.reshape(t, (tB, K, G, tT, tS))
        return t

    bias = _reshape_to_grouped(bias, "bias")
    mask = _reshape_to_grouped(mask, "mask")
    vmapped_fn = jax.vmap(
        _dot_product_attention_core,
        in_axes=(3, None, None, 2, 2, None, None),
        out_axes=3,
    )
    encoded = vmapped_fn(query, key, value, bias, mask, is_causal, scale)
    return jnp.reshape(encoded, output_shape)
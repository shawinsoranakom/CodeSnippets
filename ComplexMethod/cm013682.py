def flex_attention(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    score_mod: _score_mod_signature | None = None,
    block_mask: BlockMask | None = None,
    scale: float | None = None,
    enable_gqa: bool = False,
    return_lse: bool = False,
    kernel_options: FlexKernelOptions | None = None,
    *,
    return_aux: AuxRequest | None = None,
) -> Tensor | tuple[Tensor, Tensor] | tuple[Tensor, AuxOutput]:
    r"""This function implements scaled dot product attention with an arbitrary attention score modification function
    described in the `Flex Attention <https://arxiv.org/abs/2412.05496>`_ paper. See also the
    `blog post <https://pytorch.org/blog/flexattention/>`_.

    This function computes the scaled dot product attention between query, key, and value tensors with a user-defined
    attention score modification function. The attention score modification function will be applied after the attention
    scores have been calculated between the query and key tensors. The attention scores are calculated as follows:

    The ``score_mod`` function should have the following signature:

    .. code-block:: python

        def score_mod(
            score: Tensor,
            batch: Tensor,
            head: Tensor,
            q_idx: Tensor,
            k_idx: Tensor
        ) -> Tensor:

    Where:
        - ``score``: A scalar tensor representing the attention score,
          with the same data type and device as the query, key, and value tensors.
        - ``batch``, ``head``, ``q_idx``, ``k_idx``: Scalar tensors indicating
          the batch index, query head index, query index, and key/value index, respectively.
          These should have the ``torch.int`` data type and be located on the same device as the score tensor.

    Args:
        query (Tensor): Query tensor; shape :math:`(B, Hq, L, E)`. For FP8 dtypes, should be in row-major memory layout for optimal performance.
        key (Tensor): Key tensor; shape :math:`(B, Hkv, S, E)`. For FP8 dtypes, should be in row-major memory layout for optimal performance.
        value (Tensor): Value tensor; shape :math:`(B, Hkv, S, Ev)`. For FP8 dtypes, should be in column-major memory layout for optimal performance.
        score_mod (Optional[Callable]): Function to modify attention scores. By default no score_mod is applied.
        block_mask (Optional[BlockMask]): BlockMask object that controls the blocksparsity pattern of the attention.
        scale (Optional[float]): Scaling factor applied prior to softmax. If none, the default value is set to :math:`\frac{1}{\sqrt{E}}`.
        enable_gqa (bool): If set to True, enables Grouped Query Attention (GQA) and broadcasts key/value heads to query heads.
        return_lse (bool): Whether to return the logsumexp of the attention scores. Default is False. **Deprecated**: Use ``return_aux=AuxRequest(lse=True)`` instead.
        kernel_options (Optional[FlexKernelOptions]):
            Options to control the behavior of the underlying Triton kernels.
            See :class:`FlexKernelOptions` for available options and usage examples.
        return_aux (Optional[AuxRequest]): Specifies which auxiliary outputs to compute and return.
            If None, only the attention output is returned. Use ``AuxRequest(lse=True, max_scores=True)``
            to request both auxiliary outputs.

    Returns:
        output (Tensor): Attention output; shape :math:`(B, Hq, L, Ev)`.

        When ``return_aux`` is not None:
            aux (AuxOutput): Auxiliary outputs with requested fields populated.

        When ``return_aux`` is None (deprecated paths):
            lse (Tensor): Log-sum-exp of attention scores; shape :math:`(B, Hq, L)`. Only returned if ``return_lse=True``.

    Shape legend:
        - :math:`N: \text{Batch size} ... : \text{Any number of other batch dimensions (optional)}`
        - :math:`S: \text{Source sequence length}`
        - :math:`L: \text{Target sequence length}`
        - :math:`E: \text{Embedding dimension of the query and key}`
        - :math:`Ev: \text{Embedding dimension of the value}`

    .. warning::
        `torch.nn.attention.flex_attention` is a prototype feature in PyTorch.
        Please look forward to a more stable implementation in a future version of PyTorch.
        Read more about feature classification at: https://pytorch.org/blog/pytorch-feature-classification-changes/#prototype

    """
    # Some basic input validation
    _validate_sdpa_input(query, key, value, allow_lowp_kv=True)
    _validate_embed_dim(query, key, value)
    _validate_device(query, key, value)
    query, key, value = _enforce_mem_layouts(query, key, value)
    if query.dim() != 4 or key.dim() != 4 or value.dim() != 4:
        raise NotImplementedError("NYI: query, key, and value must be 4D tensors")
    if (not enable_gqa) and query.size(-3) != key.size(-3):
        raise ValueError(
            f"Expect query and key/value to have the same number of heads "
            f"but got Hq={query.size(-3)} and Hkv={key.size(-3)}. "
            f"Try setting enable_gqa=True for GQA."
        )
    if enable_gqa:
        Hq = query.size(1)
        Hkv = key.size(1)
        if Hq % Hkv != 0:
            raise ValueError(
                f"Expect number of query heads to be a multiple of kv heads for GQA "
                f"but got Hq={Hq} and Hkv={Hkv}."
            )
    if query.size(0) != key.size(0):
        if block_mask is None:
            raise ValueError(
                f"Expect query and key/value to have the same batch size, "
                f"or non-none block_mask, "
                f"but got block_mask=None, Bq={query.size(0)}, and Bkv={key.size(0)}."
            )

        if block_mask.kv_num_blocks.size(0) != query.size(0):
            raise ValueError(
                f"Expect query and key/value to have the same batch size, "
                f"or block_mask and query to have the same batch size, "
                f"but got Bq={query.size(0)}, Bkv={key.size(0)}, B_block_mask={block_mask.kv_num_blocks.size(0)}."
            )

    if score_mod is None:
        score_mod = _identity

    if block_mask is None:
        block_mask = _create_empty_block_mask(query, key)

    # If BlockMask was sliced, its mask_mod is intentionally replaced with an error-raising stub.
    # This guard ensures we surface the intended error message before any shape-based checks.
    if getattr(block_mask, "mask_mod", None) is _sliced_mask_mod_error:
        raise RuntimeError("Cannot use mask_mod from a sliced BlockMask")

    if (
        block_mask.BLOCK_SIZE[0] == _LARGE_SPARSE_BLOCK_SIZE
        and block_mask.BLOCK_SIZE[1] == _LARGE_SPARSE_BLOCK_SIZE
    ):
        # This corresponds to the case where we essentially have a "no-op" block mask.
        pass
    else:
        block_mask_q_len = block_mask.shape[-2]
        block_mask_kv_len = block_mask.shape[-1]
        if query.size(-2) > block_mask_q_len or key.size(-2) > block_mask_kv_len:
            raise ValueError(
                f"block_mask was created for block_mask.shape={block_mask.shape} but got q_len={query.size(-2)} and kv_len={key.size(-2)}. "
                "As the block mask was created for a smaller length than you're using it for, you likely need to create a new block mask."
            )
        elif (
            query.size(-2) < block_mask_q_len and key.size(-2) <= block_mask_kv_len
        ) or (query.size(-2) <= block_mask_q_len and key.size(-2) < block_mask_kv_len):
            raise ValueError(
                f"block_mask was created for block_mask.shape={block_mask.shape} but got q_len={query.size(-2)} and kv_len={key.size(-2)}. "
                "As the block mask was created for a larger length than you're using it for, you can either 1. create a new block mask with the correct length, or 2. 'adjust' the existing block mask to the correct length by calling block_mask._adjust(q_len, kv_len). This essentially 'crops' the block mask to the upper left corner, which does not work for all mask_mods!"
            )
        if query.size(-2) != block_mask_q_len:
            raise AssertionError(
                f"query.size(-2) ({query.size(-2)}) != block_mask_q_len ({block_mask_q_len})"
            )
        if key.size(-2) != block_mask_kv_len:
            raise AssertionError(
                f"key.size(-2) ({key.size(-2)}) != block_mask_kv_len ({block_mask_kv_len})"
            )

    if scale is None:
        scale = 1.0 / math.sqrt(query.size(-1))

    if query.device != block_mask.kv_num_blocks.device:  # type: ignore[union-attr]
        raise RuntimeError(
            f"Expect q/k/v and block_mask to be on the same device "
            f"but got {query.device} and {block_mask.kv_num_blocks.device}."  # type: ignore[union-attr]
        )

    # Handle deprecation warnings for old parameters
    if return_lse and return_aux is not None:
        raise ValueError(
            "Cannot specify both return_lse and return_aux. "
            "return_lse is deprecated, please use return_aux=AuxRequest(lse=True) instead."
        )
    elif return_lse and return_aux is None:
        _warn_once(
            "deprecated_return_lse",
            "return_lse is deprecated and will be removed in v2.10. "
            "Please use return_aux=AuxRequest(lse=True) instead.",
            category=FutureWarning,
        )

    kernel_options = _apply_kernel_options(
        query,
        key,
        value,
        return_lse,
        kernel_options,
        return_aux,
    )

    def _finalize_outputs(
        out,
        lse,
        max_scores,
        *,
        return_aux: AuxRequest | None,
        return_lse: bool,
    ):
        """Normalize stats and build return value (aux-aware, legacy-compatible)."""
        ln2 = math.log(2.0)
        return_lse = return_lse or return_aux is not None and return_aux.lse
        return_max = return_aux is not None and return_aux.max_scores

        lse_scaled = lse * ln2 if (return_lse and lse.numel() > 0) else None
        max_scaled = (
            max_scores * ln2 if (return_max and max_scores.numel() > 0) else None
        )

        if return_aux is not None:
            return out, AuxOutput(
                lse=lse_scaled,
                max_scores=max_scaled,
            )

        if return_lse:
            return out, lse_scaled

        return out

    if torch.compiler.is_dynamo_compiling():
        # mark head_dim and number of heads to be static
        for x in [query, key, value]:
            torch._dynamo.mark_static(x, -3)
            torch._dynamo.mark_static(x, -1)

        out, lse, max_scores = flex_attention_hop(
            query,
            key,
            value,
            score_mod,
            block_mask.as_tuple(),
            scale,
            kernel_options,  # type: ignore[union-attr]
        )
        return _finalize_outputs(
            out, lse, max_scores, return_aux=return_aux, return_lse=return_lse
        )

    if not _FLEX_ATTENTION_DISABLE_COMPILE_DEBUG:
        _warn_once(
            warning_id="flex_attention_performance",
            message=(
                "flex_attention called without torch.compile() - this will use an unfused implementation that materializes the full scores matrix instead of generating a fused kernel.\n\n"
                "SOLUTION: Use torch.compile(flex_attention)(...)\n\n"
                "If you want to debug your score_mod/mask_mod, you can set:\n"
                "torch.nn.attention.flex_attention._FLEX_ATTENTION_DISABLE_COMPILE_DEBUG = True\n\n"
                "This will allow you to use print statements or breakpoints. Note: This doesn't work with the backwards pass and may produce incorrect results."
            ),
        )

    if not torch._dynamo.is_dynamo_supported():
        raise RuntimeError("flex_attention requires dynamo support")

    # Dynamo is expecting a callable with "__code__" attribute.
    # We cannot directly pass hop to it. So we wrap it in a dummy function.
    def _flex_attention_hop_wrapper(*args, **kwargs):
        return flex_attention_hop(*args, **kwargs)

    with setup_compilation_env() as backend:
        if _FLEX_ATTENTION_DISABLE_COMPILE_DEBUG:
            flex_fn = _flex_attention_hop_wrapper
        else:
            flex_fn = torch.compile(
                _flex_attention_hop_wrapper, backend=backend, fullgraph=True
            )

        out, lse, max_scores = flex_fn(
            query,
            key,
            value,
            score_mod,
            block_mask.as_tuple(),
            scale,
            kernel_options,
        )
    return _finalize_outputs(
        out, lse, max_scores, return_aux=return_aux, return_lse=return_lse
    )
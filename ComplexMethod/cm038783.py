def _lazy_init() -> None:
    """Import deep_gemm and resolve symbols on first use."""
    global _fp8_gemm_nt_impl, _grouped_impl, _grouped_masked_impl
    global _fp8_mqa_logits_impl, _fp8_paged_mqa_logits_impl
    global _get_paged_mqa_logits_metadata_impl
    global _get_mn_major_tma_aligned_tensor_impl
    global _get_mk_alignment_for_contiguous_layout_impl
    global _transform_sf_into_required_layout_impl
    # fast path
    if (
        _fp8_gemm_nt_impl is not None
        or _grouped_impl is not None
        or _grouped_masked_impl is not None
        or _fp8_mqa_logits_impl is not None
        or _fp8_paged_mqa_logits_impl is not None
        or _get_paged_mqa_logits_metadata_impl is not None
        or _get_mk_alignment_for_contiguous_layout_impl is not None
        or _transform_sf_into_required_layout_impl is not None
    ):
        return

    if not has_deep_gemm():
        return

    # Set up deep_gemm cache path
    DEEP_GEMM_JIT_CACHE_ENV_NAME = "DG_JIT_CACHE_DIR"
    if not os.environ.get(DEEP_GEMM_JIT_CACHE_ENV_NAME, None):
        os.environ[DEEP_GEMM_JIT_CACHE_ENV_NAME] = os.path.join(
            envs.VLLM_CACHE_ROOT, "deep_gemm"
        )

    _dg = _import_deep_gemm()
    if _dg is None:
        return

    _fp8_gemm_nt_impl = getattr(_dg, "fp8_gemm_nt", None)
    _grouped_impl = getattr(_dg, "m_grouped_fp8_gemm_nt_contiguous", None)
    _grouped_masked_impl = getattr(_dg, "fp8_m_grouped_gemm_nt_masked", None)
    _fp8_mqa_logits_impl = getattr(_dg, "fp8_mqa_logits", None)
    _fp8_paged_mqa_logits_impl = getattr(_dg, "fp8_paged_mqa_logits", None)
    _get_paged_mqa_logits_metadata_impl = getattr(
        _dg, "get_paged_mqa_logits_metadata", None
    )
    _get_mn_major_tma_aligned_tensor_impl = getattr(
        _dg, "get_mn_major_tma_aligned_tensor", None
    )
    _get_mk_alignment_for_contiguous_layout_impl = getattr(
        _dg, "get_mk_alignment_for_contiguous_layout", None
    )
    _transform_sf_into_required_layout_impl = getattr(
        _dg, "transform_sf_into_required_layout", None
    )
    DeepGemmQuantScaleFMT.init_oracle_cache()
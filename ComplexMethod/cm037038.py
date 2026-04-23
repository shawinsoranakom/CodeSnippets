def _rocm_aiter_mla_decode_fwd_impl(
    q: torch.Tensor,
    kv_buffer: torch.Tensor,
    o: torch.Tensor,
    qo_indptr: torch.Tensor,
    max_seqlen_qo: int,
    kv_indptr: torch.Tensor | None = None,
    kv_indices: torch.Tensor | None = None,
    kv_last_page_lens: torch.Tensor | None = None,
    sm_scale: float = 1.0,
    logit_cap: float = 0.0,
    q_scale: torch.Tensor | None = None,
    kv_scale: torch.Tensor | None = None,
    work_meta_data: torch.Tensor | None = None,
    work_indptr: torch.Tensor | None = None,
    work_info_set: torch.Tensor | None = None,
    reduce_indptr: torch.Tensor | None = None,
    reduce_final_map: torch.Tensor | None = None,
    reduce_partial_map: torch.Tensor | None = None,
) -> None:
    from aiter.mla import mla_decode_fwd

    kwargs: dict[str, float | torch.Tensor | None] = {
        "sm_scale": sm_scale,
        "logit_cap": logit_cap,
    }

    # Only pass q_scale and kv_scale if the aiter library supports them
    if _check_aiter_mla_fp8_support():
        kwargs["q_scale"] = q_scale
        kwargs["kv_scale"] = kv_scale

    if work_meta_data is not None:
        assert work_indptr is not None, (
            "work_indptr must be provided with work_meta_data"
        )
        assert work_info_set is not None, (
            "work_info_set must be provided with work_meta_data"
        )
        assert reduce_indptr is not None, (
            "reduce_indptr must be provided with work_meta_data"
        )
        assert reduce_final_map is not None, (
            "reduce_final_map must be provided with work_meta_data"
        )
        assert reduce_partial_map is not None, (
            "reduce_partial_map must be provided with work_meta_data"
        )
        kwargs["work_meta_data"] = work_meta_data
        kwargs["work_indptr"] = work_indptr
        kwargs["work_info_set"] = work_info_set
        kwargs["reduce_indptr"] = reduce_indptr
        kwargs["reduce_final_map"] = reduce_final_map
        kwargs["reduce_partial_map"] = reduce_partial_map

    mla_decode_fwd(
        q,
        kv_buffer.view(-1, 1, 1, q.shape[-1]),
        o,
        qo_indptr,
        kv_indptr,
        kv_indices,
        kv_last_page_lens,
        max_seqlen_qo,
        **kwargs,
    )
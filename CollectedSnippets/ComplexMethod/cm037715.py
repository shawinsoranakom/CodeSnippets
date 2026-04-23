def __init__(
        self,
        num_heads: int,
        head_size: int,
        scale: float,
        num_kv_heads: int,
        alibi_slopes: list[float] | None,
        sliding_window: int | None,
        kv_cache_dtype: str,
        logits_soft_cap: float | None,
        attn_type: str,
        kv_sharing_target_layer_name: str | None,
        # MLA Specific Arguments
        q_lora_rank: int | None,
        kv_lora_rank: int,
        qk_nope_head_dim: int,
        qk_rope_head_dim: int,
        qk_head_dim: int,
        v_head_dim: int,
        kv_b_proj: ColumnParallelLinear,
        indexer: object | None = None,
        q_pad_num_heads: int | None = None,
    ) -> None:
        if kv_sharing_target_layer_name is not None:
            raise NotImplementedError("KV sharing is not supported for MLA")

        self.num_heads = num_heads
        self.head_size = head_size
        self.scale = float(scale)
        self.num_kv_heads = num_kv_heads
        self.kv_cache_dtype = kv_cache_dtype

        self.q_lora_rank = q_lora_rank
        self.kv_lora_rank = kv_lora_rank
        self.qk_nope_head_dim = qk_nope_head_dim
        self.qk_rope_head_dim = qk_rope_head_dim
        self.qk_head_dim = qk_head_dim
        self.v_head_dim = v_head_dim
        self.kv_b_proj = kv_b_proj
        self.indexer = indexer
        self.q_pad_num_heads = q_pad_num_heads
        self.supports_quant_query_input = True

        # Use flashinfer's optimized concat_mla_k kernel when available.
        # The kernel is optimized for DeepSeek V3 dimensions:
        # num_heads=128, nope_dim=128, rope_dim=64
        self._use_flashinfer_concat_mla_k = (
            has_flashinfer()
            and (self.num_heads == 128)
            and (self.qk_nope_head_dim == 128)
            and (self.qk_rope_head_dim == 64)
        )

        if use_trtllm_ragged_deepseek_prefill():
            logger.info_once("Using TRT-LLM ragged DeepSeek prefill for MLA")
            self._run_prefill_context_chunk = (
                self._run_prefill_context_chunk_trtllm_ragged
            )
            self._run_prefill_new_tokens = self._run_prefill_new_tokens_trtllm_ragged
            self._pad_v = False
        elif use_flashinfer_prefill():
            logger.info_once("Using FlashInfer prefill for MLA")
            self._run_prefill_context_chunk = self._run_prefill_context_chunk_fi
            self._run_prefill_new_tokens = self._run_prefill_new_tokens_fi
            self._pad_v = False
        elif use_cudnn_prefill():
            logger.info_once("Using CUDNN prefill for MLA")
            self._run_prefill_context_chunk = self._run_prefill_context_chunk_cudnn
            self._run_prefill_new_tokens = self._run_prefill_new_tokens_cudnn
            self._pad_v = False
        else:  # Use FlashAttention
            if flash_attn_varlen_func is None:
                raise RuntimeError(
                    "MLA attention requires FlashAttention but it is not "
                    "available. Please install flash_attn or use "
                    "--attention-backend ROCM_AITER_MLA."
                )
            logger.info_once("Using FlashAttention prefill for MLA")
            self._run_prefill_context_chunk = self._run_prefill_context_chunk_fa
            self._run_prefill_new_tokens = self._run_prefill_new_tokens_fa

            # Handle the differences between the flash_attn_varlen from
            # flash_attn and the one from vllm_flash_attn. The former is used on
            # RoCM and the latter has an additional parameter to control
            # FA2 vs FA3
            self.flash_attn_varlen_func = flash_attn_varlen_func
            self.vllm_flash_attn_version = get_flash_attn_version(
                head_size=self.qk_head_dim
            )
            if self.vllm_flash_attn_version is not None:
                self.flash_attn_varlen_func = functools.partial(
                    flash_attn_varlen_func, fa_version=self.vllm_flash_attn_version
                )

            # For MLA the v head dim is smaller than qk head dim so we pad out
            # v with 0s to match the qk head dim for attention backends that do
            # not support different headdims.
            # FA3 on Hopper (SM90) and FA4 natively handle diff headdims.
            device_capability = current_platform.get_device_capability()
            self._pad_v = self.vllm_flash_attn_version is None or not (
                (
                    self.vllm_flash_attn_version == 3
                    and device_capability is not None
                    and device_capability[0] == 9
                )
                or self.vllm_flash_attn_version == 4
            )

        self.dcp_world_size: int = -1

        self.cp_kv_cache_interleave_size: int = (
            get_current_vllm_config().parallel_config.cp_kv_cache_interleave_size
        )
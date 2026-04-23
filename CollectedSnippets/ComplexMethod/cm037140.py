def __init__(self, config: VllmConfig) -> None:
        super().__init__(config)
        self.disabled = True

        if _MINIMAX_QK_NORM_FUSED_OP is None:
            logger.warning_once(
                "minimax_allreduce_rms_qk op not found, MiniMaxQKNormPass disabled."
            )
            return

        tp_world = get_tensor_model_parallel_world_size()
        if tp_world <= 1:
            logger.warning_once("MiniMaxQKNormPass disabled: tp_size <= 1.")
            return

        if config.model_config is None:
            logger.warning_once("MiniMaxQKNormPass disabled: no model_config.")
            return

        hf_cfg = config.model_config.hf_config

        model_name = getattr(hf_cfg, "architectures", "")[0]
        if model_name != "MiniMaxM2ForCausalLM":
            return

        num_attention_heads = getattr(hf_cfg, "num_attention_heads", 0)
        num_key_value_heads = getattr(hf_cfg, "num_key_value_heads", 0)
        hidden_size = getattr(hf_cfg, "hidden_size", 0)
        head_dim = getattr(hf_cfg, "head_dim", 0)
        eps: float = getattr(hf_cfg, "rms_norm_eps", 1e-6)

        if (
            num_attention_heads != 48
            or num_key_value_heads != 8
            or hidden_size != 3072
            or head_dim != 128
        ):
            logger.warning_once(
                "MiniMaxQKNormPass disabled: cannot infer model info from hf_config."
            )
            return

        num_heads_per_rank = num_attention_heads // tp_world
        num_kv_heads_per_rank = max(1, num_key_value_heads // tp_world)
        q_size = num_heads_per_rank * head_dim
        kv_size = num_kv_heads_per_rank * head_dim

        self.max_token_num = min(
            MAX_TOKEN_NUM, config.scheduler_config.max_num_batched_tokens
        )

        tp_rank = get_tensor_model_parallel_rank()
        # Allocate Lamport workspace first.
        from vllm.distributed.parallel_state import get_tp_group
        from vllm.model_executor.layers.mamba.lamport_workspace import (
            get_allreduce_workspace,
        )

        get_allreduce_workspace(
            rank=tp_rank,
            world_size=tp_world,
            max_tokens=self.max_token_num,
            process_group=get_tp_group().cpu_group,
        )

        self.patterns: PatternMatcherPass = PatternMatcherPass(
            pass_name="minimax_qk_norm_pass"
        )
        self._register_patterns(q_size, kv_size, eps, tp_world, tp_rank)
        self.dump_patterns(config, self.patterns)
        self.disabled = False
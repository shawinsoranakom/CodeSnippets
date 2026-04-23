def __init__(
        self,
        config: PretrainedConfig,
        quant_config: QuantizationConfig | None = None,
        layer_id: int = -1,
        prefix: str = "",
        enable_eplb: bool = False,
    ):
        super().__init__()
        self.tp_size = get_tensor_model_parallel_world_size()

        self.ep_group = get_ep_group().device_group
        self.ep_rank = get_ep_group().rank_in_group
        self.ep_size = self.ep_group.size()
        self.n_routed_experts = config.num_experts

        if self.tp_size > config.num_experts:
            raise ValueError(
                f"Tensor parallel size {self.tp_size} is greater than "
                f"the number of experts {config.num_experts}."
            )

        # Get layer_id topk if config.moe_topk is a list
        if isinstance(config.moe_topk, list):
            assert layer_id >= 0
            assert len(config.moe_topk) > layer_id
            top_k = config.moe_topk[layer_id]
        else:
            top_k = config.moe_topk

        # If it is moe, moe_intermediate_size is preferred
        intermediate_size = config.intermediate_size
        if config.moe_intermediate_size is not None:
            intermediate_size = (
                config.moe_intermediate_size
                if isinstance(config.moe_intermediate_size, int)
                else config.moe_intermediate_size[layer_id]
            )

        # Load balancing settings.
        vllm_config = get_current_vllm_config()
        eplb_config = vllm_config.parallel_config.eplb_config
        self.enable_eplb = enable_eplb

        self.n_logical_experts = self.n_routed_experts
        self.n_redundant_experts = eplb_config.num_redundant_experts
        self.n_physical_experts = self.n_logical_experts + self.n_redundant_experts
        self.n_local_physical_experts = self.n_physical_experts // self.ep_size
        self.physical_expert_start = self.ep_rank * self.n_local_physical_experts
        self.physical_expert_end = (
            self.physical_expert_start + self.n_local_physical_experts
        )

        self.gate = ReplicatedLinear(
            config.hidden_size,
            config.num_experts,
            bias=False,
            quant_config=None,
            prefix=f"{prefix}.gate",
        )
        if config.use_mixed_mlp_moe > 0:
            # Get layer_id num_shared_expert if config.num_shared_expert is
            # a list.
            if isinstance(config.num_shared_expert, list):
                assert layer_id >= 0
                assert len(config.num_shared_expert) > layer_id
                num_shared_expert = config.num_shared_expert[layer_id]
            else:
                num_shared_expert = config.num_shared_expert

            self.shared_mlp = HunYuanMLP(
                hidden_size=config.hidden_size,
                intermediate_size=config.intermediate_size * num_shared_expert,
                hidden_act=config.hidden_act,
                quant_config=quant_config,
                reduce_results=False,
                prefix=f"{prefix}.shared_mlp",
            )
        else:
            self.shared_mlp = None

        self.experts = FusedMoE(
            shared_experts=self.shared_mlp,
            num_experts=self.n_routed_experts,
            top_k=top_k,
            hidden_size=config.hidden_size,
            intermediate_size=intermediate_size,
            renormalize=top_k > 1,
            quant_config=quant_config,
            prefix=f"{prefix}.experts",
            enable_eplb=self.enable_eplb,
            num_redundant_experts=self.n_redundant_experts,
        )
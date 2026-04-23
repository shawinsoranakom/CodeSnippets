def __init__(
        self,
        vllm_config: VllmConfig,
        prefix: str = "",
    ):
        super().__init__()

        self.tp_size = get_tensor_model_parallel_world_size()
        self.layer_idx = extract_layer_index(prefix)

        self.ep_size = get_ep_group().device_group.size()
        self.ep_rank = get_ep_group().device_group.rank()
        config = vllm_config.model_config.hf_config
        quant_config = vllm_config.quant_config
        parallel_config = vllm_config.parallel_config

        self.hidden_size = config.hidden_size
        self.enable_eplb = parallel_config.enable_eplb
        self.n_routed_experts = config.moe_num_experts
        self.n_logical_experts = self.n_routed_experts
        self.n_redundant_experts = parallel_config.eplb_config.num_redundant_experts
        self.n_physical_experts = self.n_logical_experts + self.n_redundant_experts
        self.n_local_physical_experts = self.n_physical_experts // self.ep_size

        self.physical_expert_start = self.ep_rank * self.n_local_physical_experts
        self.physical_expert_end = (
            self.physical_expert_start + self.n_local_physical_experts
        )

        if self.tp_size > config.moe_num_experts:
            raise ValueError(
                f"Tensor parallel size {self.tp_size} is greater than "
                f"the number of experts {config.moe_num_experts}."
            )

        self.gate = FP32ReplicatedLinear(
            config.hidden_size,
            config.moe_num_experts,
            bias=False,
            quant_config=None,
            params_dtype=torch.float32,  # Use FP32 for higher precision.
            prefix=f"{prefix}.gate",
        )
        self.use_moe_router_bias = config.use_moe_router_bias
        assert self.use_moe_router_bias, "Only support use_moe_router_bias is true."
        self.routed_scaling_factor = config.moe_router_scaling_factor
        self.router_bias = nn.Parameter(
            torch.zeros(config.moe_num_experts, dtype=torch.float32),
            requires_grad=False,
        )
        self.need_fp32_gate = config.need_fp32_gate
        assert self.need_fp32_gate, (
            "Router logits must use FP32 precision for numerical stability."
        )

        activation = "silu"
        swiglu_limits = config.swiglu_limits or []
        swiglu_limit = (
            swiglu_limits[self.layer_idx]
            if self.layer_idx < len(swiglu_limits)
            else None
        )
        if swiglu_limit not in (None, 0):
            swiglu_limit = float(swiglu_limit)
            assert swiglu_limit == 7.0, (
                "Swiglu limit in fused moe block only support 7.0 now."
            )
            activation = "swiglustep"
            logger.debug(
                "step3p5 layer_idx: %s, activation: %s, limit: %s",
                self.layer_idx,
                activation,
                swiglu_limit,
            )

        self.share_expert = Step3p5MLP(
            config=config,
            hidden_size=self.hidden_size,
            intermediate_size=config.share_expert_dim,
            hidden_act="silu",
            reduce_results=False,
            quant_config=quant_config,
            prefix=f"{prefix}.share_expert",
        )
        self.experts = FusedMoE(
            shared_experts=self.share_expert,
            gate=self.gate,
            num_experts=config.moe_num_experts,
            top_k=config.moe_top_k,
            hidden_size=config.hidden_size,
            intermediate_size=config.moe_intermediate_size,
            renormalize=config.norm_expert_weight,
            quant_config=quant_config,
            activation=activation,
            prefix=f"{prefix}.experts",
            scoring_func=getattr(config, "moe_router_activation", "sigmoid"),
            e_score_correction_bias=self.router_bias,
            routed_scaling_factor=config.moe_router_scaling_factor,
            enable_eplb=self.enable_eplb,
            num_redundant_experts=self.n_redundant_experts,
            router_logits_dtype=torch.float32,
        )
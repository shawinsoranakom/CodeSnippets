def __init__(
        self,
        intermediate_size: int,
        config: PretrainedConfig,
        quant_config: QuantizationConfig | None = None,
        reduce_results: bool | None = True,
        prefix: str = "",
    ):
        super().__init__()

        self.tp_size = get_tensor_model_parallel_world_size()
        self.tp_rank = get_tensor_model_parallel_rank()
        self.num_experts = config.num_experts
        self.top_k = config.num_experts_per_tok
        self.norm_expert_prob = config.norm_topk_prob
        self.hidden_size = config.hidden_size
        self.quant_config = quant_config
        self.num_shared_experts = config.num_shared_experts
        self.score_function = getattr(config, "score_function", None)
        self.n_group = getattr(config, "n_group", None)
        self.topk_group = getattr(config, "topk_group", None)
        self.use_grouped_topk = self.n_group is not None and self.topk_group is not None
        self.routed_scaling_factor = getattr(config, "routed_scaling_factor", 1.0)

        router_dtype = getattr(config, "router_dtype", None)
        if router_dtype is None:
            self.router_dtype = None
        elif router_dtype == "fp32":
            self.router_dtype = torch.float32
        else:
            self.router_dtype = torch.bfloat16

        self.gate = nn.Linear(
            self.hidden_size,
            self.num_experts,
            bias=False,
            dtype=self.router_dtype,
        )

        if getattr(config, "moe_router_enable_expert_bias", False):
            self.gate.expert_bias = nn.Parameter(
                torch.empty((config.num_experts,), dtype=torch.float32)
            )
        else:
            self.gate.expert_bias = None

        self.correction_bias = (
            self.gate.expert_bias.data if self.gate.expert_bias is not None else None
        )

        if self.score_function is not None:
            assert (
                self.score_function == "softmax" and self.correction_bias is None
            ) or (
                self.score_function == "sigmoid" and self.correction_bias is not None
            ), (
                "score_function and correction_bias should be in 2 combination (softmax, None) or (sigmoid, not None)"  # noqa: E501
            )
        else:
            # default value for scoring_func
            self.score_function = "softmax"

        if self.num_shared_experts > 0:
            if hasattr(config, "moe_shared_expert_intermediate_size"):
                intermediate_size = config.moe_shared_expert_intermediate_size
            else:
                intermediate_size = config.moe_intermediate_size
            intermediate_size *= config.num_shared_experts
            self.shared_experts = BailingMLP(
                intermediate_size=intermediate_size,
                config=config,
                quant_config=quant_config,
                reduce_results=False,
                prefix=f"{prefix}.shared_experts",
            )
        else:
            self.shared_experts = None

        self.experts = FusedMoE(
            shared_experts=self.shared_experts,
            num_experts=self.num_experts,
            top_k=self.top_k,
            hidden_size=self.hidden_size,
            intermediate_size=config.moe_intermediate_size,
            renormalize=self.norm_expert_prob,
            quant_config=quant_config,
            prefix=f"{prefix}.experts",
            scoring_func=self.score_function,
            e_score_correction_bias=self.gate.expert_bias,
            num_expert_group=self.n_group,
            topk_group=self.topk_group,
            use_grouped_topk=self.use_grouped_topk,
            router_logits_dtype=self.router_dtype,
            routed_scaling_factor=self.routed_scaling_factor,
        )
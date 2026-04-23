def __init__(
        self,
        config: PretrainedConfig,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ):
        super().__init__()

        layer_idx = extract_layer_index(prefix)
        self.layer_idx = layer_idx
        self.tp_size = get_tensor_model_parallel_world_size()
        self.has_shared_experts = getattr(config, "moe_num_shared_experts", 0) > 0
        self.hidden_size = config.hidden_size

        moe_num_experts = config.moe_num_experts
        max_moe_num_experts = max(moe_num_experts)

        if self.tp_size > max_moe_num_experts:
            raise ValueError(
                f"Tensor parallel size {self.tp_size} is greater than "
                f"the number of experts {moe_num_experts}."
            )

        moe_layer_start_index = config.moe_layer_start_index
        text_moe_layer_start_index = moe_layer_start_index[0]
        vision_moe_layer_start_index = moe_layer_start_index[1]
        moe_layer_end_index = config.moe_layer_end_index
        moe_layer_end_index = getattr(
            config,
            "moe_layer_end_index",
            [config.num_hidden_layers - 1, config.num_hidden_layers - 1],
        )
        text_moe_layer_end_index = moe_layer_end_index[0]
        vision_moe_layer_end_index = moe_layer_end_index[1]

        assert config.moe_num_experts[0] == config.moe_num_experts[1]
        self.e_score_correction_bias = nn.Parameter(
            torch.empty(2, config.moe_num_experts[0], dtype=torch.float32)
        )

        assert text_moe_layer_start_index <= text_moe_layer_end_index

        if self.has_shared_experts:
            intermediate_size = (
                config.moe_intermediate_size[0] * config.moe_num_shared_experts
            )
            self.shared_experts = Ernie4_5_VLMoeMLP(
                hidden_size=config.hidden_size,
                intermediate_size=intermediate_size,
                hidden_act=config.hidden_act,
                quant_config=quant_config,
                prefix=f"{prefix}.shared_experts",
                reduce_results=False,
            )
        else:
            self.shared_experts = None

        if (
            layer_idx >= text_moe_layer_start_index
            and layer_idx <= text_moe_layer_end_index
        ):
            self.text_experts_gate = ReplicatedLinear(
                config.hidden_size,
                config.moe_num_experts[0],
                bias=False,
                params_dtype=torch.float32,
                quant_config=quant_config,
                prefix=f"{prefix}.text_experts_gate",
            )

            self.text_experts = FusedMoE(
                shared_experts=self.shared_experts,
                num_experts=config.moe_num_experts[0],
                top_k=config.moe_k,
                hidden_size=config.hidden_size,
                intermediate_size=config.moe_intermediate_size[0],
                renormalize=True,
                quant_config=quant_config,
                e_score_correction_bias=self.e_score_correction_bias[0],
                prefix=f"{prefix}.text_experts",
                router_logits_dtype=torch.float32,
            )
        else:
            self.text_experts = Ernie4_5_VLMoeMLP(
                shared_experts=self.shared_experts,
                hidden_size=config.hidden_size,
                intermediate_size=config.intermediate_size,
                hidden_act=config.hidden_act,
                use_bias=getattr(config, "use_bias", False),
                quant_config=quant_config,
                prefix=f"{prefix}.mlp",
            )

        assert vision_moe_layer_start_index <= vision_moe_layer_end_index
        if (
            layer_idx >= vision_moe_layer_start_index
            and layer_idx <= vision_moe_layer_end_index
        ):
            self.vision_experts_gate = ReplicatedLinear(
                config.hidden_size,
                config.moe_num_experts[1],
                bias=False,
                params_dtype=torch.float32,
                quant_config=quant_config,
                prefix=f"{prefix}.vision_experts_gate",
            )

            self.vision_experts = FusedMoE(
                shared_experts=self.shared_experts,
                num_experts=config.moe_num_experts[1],
                top_k=config.moe_k,
                hidden_size=config.hidden_size,
                intermediate_size=config.moe_intermediate_size[1],
                renormalize=True,
                quant_config=quant_config,
                e_score_correction_bias=self.e_score_correction_bias[1],
                prefix=f"{prefix}.vision_experts",
                router_logits_dtype=torch.float32,
            )
        else:
            self.vision_experts = Ernie4_5_VLMoeMLP(
                shared_experts=self.shared_experts,
                hidden_size=config.hidden_size,
                intermediate_size=config.intermediate_size,
                hidden_act=config.hidden_act,
                use_bias=getattr(config, "use_bias", False),
                quant_config=quant_config,
                prefix=f"{prefix}.mlp",
            )
def __init__(
        self,
        config,
        block_size: tuple[int, int] | None = None,
        activation_scheme: str = "dynamic",
        has_bias: bool = False,
        has_gate: bool = True,
        dtype=_FP8_DTYPE,
    ):
        super().__init__()

        assert has_bias is False, (
            "FP8Experts does not support bias for now, please open an issue if you want this feature"
        )

        self.config = config
        self.has_bias = has_bias
        self.has_gate = has_gate
        self.block_size = block_size
        self.hidden_dim = config.hidden_size
        self.activation_scheme = activation_scheme
        self.num_experts = getattr(config, "num_local_experts", config.num_experts)
        self.intermediate_dim = getattr(config, "moe_intermediate_size", config.intermediate_size)
        self.act_fn = ACT2FN[getattr(config, "hidden_activation", config.hidden_act)]

        if self.has_gate:
            gu_proj_out, gu_proj_in = 2 * self.intermediate_dim, self.hidden_dim
            self.gate_up_proj = nn.Parameter(torch.empty(self.num_experts, gu_proj_out, gu_proj_in, dtype=dtype))
            gu_scale_out = triton.cdiv(gu_proj_out, self.block_size[0]) if self.block_size is not None else 1
            gu_scale_in = triton.cdiv(gu_proj_in, self.block_size[1]) if self.block_size is not None else 1
            self.gate_up_proj_scale_inv = nn.Parameter(
                torch.empty(self.num_experts, gu_scale_out, gu_scale_in, dtype=torch.float32)
            )
            self.register_parameter("gate_up_proj_bias", None)
        else:
            u_proj_out, u_proj_in = self.intermediate_dim, self.hidden_dim
            self.up_proj = nn.Parameter(torch.empty(self.num_experts, u_proj_out, u_proj_in, dtype=dtype))
            u_scale_out = triton.cdiv(u_proj_out, self.block_size[0]) if self.block_size is not None else 1
            u_scale_in = triton.cdiv(u_proj_in, self.block_size[1]) if self.block_size is not None else 1
            self.up_proj_scale_inv = nn.Parameter(
                torch.empty(self.num_experts, u_scale_out, u_scale_in, dtype=torch.float32)
            )
            self.register_parameter("up_proj_bias", None)

        d_proj_out, d_proj_in = self.hidden_dim, self.intermediate_dim
        self.down_proj = nn.Parameter(torch.empty(self.num_experts, d_proj_out, d_proj_in, dtype=dtype))
        d_scale_out = triton.cdiv(d_proj_out, self.block_size[0]) if self.block_size is not None else 1
        d_scale_in = triton.cdiv(d_proj_in, self.block_size[1]) if self.block_size is not None else 1
        self.down_proj_scale_inv = nn.Parameter(
            torch.empty(self.num_experts, d_scale_out, d_scale_in, dtype=torch.float32)
        )
        self.register_parameter("down_proj_bias", None)

        if self.activation_scheme == "static":
            self.gate_up_proj_activation_scale = nn.Parameter(torch.ones(self.num_experts, dtype=torch.float32))
            self.down_proj_activation_scale = nn.Parameter(torch.ones(self.num_experts, dtype=torch.float32))
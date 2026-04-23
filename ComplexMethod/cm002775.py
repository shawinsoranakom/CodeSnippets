def __init__(self, config: PatchTSTConfig):
        super().__init__()

        self.channel_attention = config.channel_attention

        self.self_attn = PatchTSTAttention(
            embed_dim=config.d_model,
            num_heads=config.num_attention_heads,
            dropout=config.attention_dropout,
            config=config,
        )

        # Add & Norm of the sublayer 1
        self.dropout_path1 = nn.Dropout(config.path_dropout) if config.path_dropout > 0 else nn.Identity()
        if config.norm_type == "batchnorm":
            self.norm_sublayer1 = PatchTSTBatchNorm(config)
        elif config.norm_type == "layernorm":
            self.norm_sublayer1 = nn.LayerNorm(config.d_model, eps=config.norm_eps)
        else:
            raise ValueError(f"{config.norm_type} is not a supported norm layer type.")

        # Add & Norm of the sublayer 2
        if self.channel_attention:
            self.dropout_path2 = nn.Dropout(config.path_dropout) if config.path_dropout > 0 else nn.Identity()
            if config.norm_type == "batchnorm":
                self.norm_sublayer2 = PatchTSTBatchNorm(config)
            elif config.norm_type == "layernorm":
                self.norm_sublayer2 = nn.LayerNorm(config.d_model, eps=config.norm_eps)
            else:
                raise ValueError(f"{config.norm_type} is not a supported norm layer type.")

        # Position-wise Feed-Forward
        self.ff = nn.Sequential(
            nn.Linear(config.d_model, config.ffn_dim, bias=config.bias),
            ACT2CLS[config.activation_function](),
            nn.Dropout(config.ff_dropout) if config.ff_dropout > 0 else nn.Identity(),
            nn.Linear(config.ffn_dim, config.d_model, bias=config.bias),
        )

        # Add & Norm of sublayer 3
        self.dropout_path3 = nn.Dropout(config.path_dropout) if config.path_dropout > 0 else nn.Identity()
        if config.norm_type == "batchnorm":
            self.norm_sublayer3 = PatchTSTBatchNorm(config)
        elif config.norm_type == "layernorm":
            self.norm_sublayer3 = nn.LayerNorm(config.d_model, eps=config.norm_eps)
        else:
            raise ValueError(f"{config.norm_type} is not a supported norm layer type.")

        self.pre_norm = config.pre_norm
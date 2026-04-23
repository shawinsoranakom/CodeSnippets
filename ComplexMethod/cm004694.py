def __init__(self, config: DeformableDetrConfig):
        super().__init__(config)

        # Create backbone
        self.backbone = DeformableDetrConvEncoder(config)

        # Create positional encoding
        if config.position_embedding_type == "sine":
            self.position_embedding = DeformableDetrSinePositionEmbedding(config.d_model // 2, normalize=True)
        elif config.position_embedding_type == "learned":
            self.position_embedding = DeformableDetrLearnedPositionEmbedding(config.d_model // 2)
        else:
            raise ValueError(f"Not supported {config.position_embedding_type}")

        # Create input projection layers
        if config.num_feature_levels > 1:
            num_backbone_outs = len(self.backbone.intermediate_channel_sizes)
            input_proj_list = []
            for _ in range(num_backbone_outs):
                in_channels = self.backbone.intermediate_channel_sizes[_]
                input_proj_list.append(
                    nn.Sequential(
                        nn.Conv2d(in_channels, config.d_model, kernel_size=1),
                        nn.GroupNorm(32, config.d_model),
                    )
                )
            for _ in range(config.num_feature_levels - num_backbone_outs):
                input_proj_list.append(
                    nn.Sequential(
                        nn.Conv2d(
                            in_channels,
                            config.d_model,
                            kernel_size=3,
                            stride=2,
                            padding=1,
                        ),
                        nn.GroupNorm(32, config.d_model),
                    )
                )
                in_channels = config.d_model
            self.input_proj = nn.ModuleList(input_proj_list)
        else:
            self.input_proj = nn.ModuleList(
                [
                    nn.Sequential(
                        nn.Conv2d(
                            self.backbone.intermediate_channel_sizes[-1],
                            config.d_model,
                            kernel_size=1,
                        ),
                        nn.GroupNorm(32, config.d_model),
                    )
                ]
            )

        if not config.two_stage:
            self.query_position_embeddings = nn.Embedding(config.num_queries, config.d_model * 2)

        self.encoder = DeformableDetrEncoder(config)
        self.decoder = DeformableDetrDecoder(config)

        self.level_embed = nn.Parameter(torch.Tensor(config.num_feature_levels, config.d_model))

        if config.two_stage:
            self.enc_output = nn.Linear(config.d_model, config.d_model)
            self.enc_output_norm = nn.LayerNorm(config.d_model)
            self.pos_trans = nn.Linear(config.d_model * 2, config.d_model * 2)
            self.pos_trans_norm = nn.LayerNorm(config.d_model * 2)
        else:
            self.reference_points = nn.Linear(config.d_model, 2)

        self.post_init()
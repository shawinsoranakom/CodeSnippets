def __init__(self, config: GroundingDinoConfig):
        super().__init__(config)

        # Create backbone + positional encoding
        backbone = GroundingDinoConvEncoder(config)
        position_embeddings = build_position_encoding(config)
        self.backbone = GroundingDinoConvModel(backbone, position_embeddings)

        # Create input projection layers
        if config.num_feature_levels > 1:
            num_backbone_outs = len(backbone.intermediate_channel_sizes)
            input_proj_list = []
            for i in range(num_backbone_outs):
                in_channels = backbone.intermediate_channel_sizes[i]
                input_proj_list.append(
                    nn.Sequential(
                        nn.Conv2d(in_channels, config.d_model, kernel_size=1),
                        nn.GroupNorm(32, config.d_model),
                    )
                )
            for _ in range(config.num_feature_levels - num_backbone_outs):
                input_proj_list.append(
                    nn.Sequential(
                        nn.Conv2d(in_channels, config.d_model, kernel_size=3, stride=2, padding=1),
                        nn.GroupNorm(32, config.d_model),
                    )
                )
                in_channels = config.d_model
            self.input_proj_vision = nn.ModuleList(input_proj_list)
        else:
            self.input_proj_vision = nn.ModuleList(
                [
                    nn.Sequential(
                        nn.Conv2d(backbone.intermediate_channel_sizes[-1], config.d_model, kernel_size=1),
                        nn.GroupNorm(32, config.d_model),
                    )
                ]
            )

        # Create text backbone
        self.text_backbone = AutoModel.from_config(config.text_config, add_pooling_layer=False)
        self.text_projection = nn.Linear(config.text_config.hidden_size, config.d_model)

        if config.embedding_init_target or not config.two_stage:
            self.query_position_embeddings = nn.Embedding(config.num_queries, config.d_model)

        self.encoder = GroundingDinoEncoder(config)
        self.decoder = GroundingDinoDecoder(config)

        self.level_embed = nn.Parameter(torch.Tensor(config.num_feature_levels, config.d_model))

        if config.two_stage:
            self.enc_output = nn.Linear(config.d_model, config.d_model)
            self.enc_output_norm = nn.LayerNorm(config.d_model, config.layer_norm_eps)
            if (
                config.two_stage_bbox_embed_share
                and config.decoder_bbox_embed_share
                and self.decoder.bbox_embed is not None
            ):
                self.encoder_output_bbox_embed = self.decoder.bbox_embed
            else:
                self.encoder_output_bbox_embed = GroundingDinoMLPPredictionHead(
                    input_dim=config.d_model, hidden_dim=config.d_model, output_dim=4, num_layers=3
                )

            self.encoder_output_class_embed = GroundingDinoContrastiveEmbedding(config)
        else:
            self.reference_points = nn.Embedding(config.num_queries, 4)

        self.post_init()
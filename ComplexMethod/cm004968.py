def __init__(self, config: PPDocLayoutV3Config):
        super().__init__(config)

        # Create backbone
        self.backbone = PPDocLayoutV3ConvEncoder(config)
        intermediate_channel_sizes = self.backbone.intermediate_channel_sizes

        # Create encoder input projection layers
        # https://github.com/lyuwenyu/RT-DETR/blob/94f5e16708329d2f2716426868ec89aa774af016/PPDocLayoutV3_pytorch/src/zoo/PPDocLayoutV3/hybrid_encoder.py#L212
        num_backbone_outs = len(intermediate_channel_sizes)

        encoder_input_proj_list = []
        for i in range(num_backbone_outs):
            in_channels = intermediate_channel_sizes[i]
            encoder_input_proj_list.append(
                nn.Sequential(
                    nn.Conv2d(in_channels, config.encoder_hidden_dim, kernel_size=1, bias=False),
                    nn.BatchNorm2d(config.encoder_hidden_dim),
                )
            )
        self.encoder_input_proj = nn.ModuleList(encoder_input_proj_list[1:])

        # Create encoder
        self.encoder = PPDocLayoutV3HybridEncoder(config)

        # denoising part
        if config.num_denoising > 0:
            self.denoising_class_embed = nn.Embedding(
                config.num_labels + 1, config.d_model, padding_idx=config.num_labels
            )

        # decoder embedding
        if config.learn_initial_query:
            self.weight_embedding = nn.Embedding(config.num_queries, config.d_model)

        # encoder head
        self.enc_output = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.LayerNorm(config.d_model, eps=config.layer_norm_eps),
        )
        self.enc_score_head = nn.Linear(config.d_model, config.num_labels)
        self.enc_bbox_head = PPDocLayoutV3MLPPredictionHead(config.d_model, config.d_model, 4, num_layers=3)

        # init encoder output anchors and valid_mask
        if config.anchor_image_size:
            self.anchors, self.valid_mask = self.generate_anchors(dtype=self.dtype)

        # Create decoder input projection layers
        # https://github.com/lyuwenyu/RT-DETR/blob/94f5e16708329d2f2716426868ec89aa774af016/PPDocLayoutV3_pytorch/src/zoo/PPDocLayoutV3/PPDocLayoutV3_decoder.py#L412
        num_backbone_outs = len(config.decoder_in_channels)
        decoder_input_proj_list = []
        for i in range(num_backbone_outs):
            in_channels = config.decoder_in_channels[i]
            decoder_input_proj_list.append(
                nn.Sequential(
                    nn.Conv2d(in_channels, config.d_model, kernel_size=1, bias=False),
                    nn.BatchNorm2d(config.d_model, config.batch_norm_eps),
                )
            )
        for _ in range(config.num_feature_levels - num_backbone_outs):
            decoder_input_proj_list.append(
                nn.Sequential(
                    nn.Conv2d(in_channels, config.d_model, kernel_size=3, stride=2, padding=1, bias=False),
                    nn.BatchNorm2d(config.d_model, config.batch_norm_eps),
                )
            )
            in_channels = config.d_model
        self.decoder_input_proj = nn.ModuleList(decoder_input_proj_list)
        self.decoder = PPDocLayoutV3Decoder(config)

        self.decoder_order_head = nn.ModuleList(
            [nn.Linear(config.d_model, config.d_model) for _ in range(config.decoder_layers)]
        )
        self.decoder_global_pointer = PPDocLayoutV3GlobalPointer(config)
        self.decoder_norm = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        self.decoder.class_embed = nn.Linear(config.d_model, config.num_labels)
        self.decoder.bbox_embed = PPDocLayoutV3MLPPredictionHead(config.d_model, config.d_model, 4, num_layers=3)

        self.mask_enhanced = config.mask_enhanced
        self.mask_query_head = PPDocLayoutV3MLPPredictionHead(
            config.d_model, config.d_model, config.num_prototypes, num_layers=3
        )

        self.post_init()
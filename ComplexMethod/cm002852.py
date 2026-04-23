def __init__(self, config: DFineConfig):
        super().__init__(config)

        # Create backbone
        self.backbone = DFineConvEncoder(config)
        intermediate_channel_sizes = self.backbone.intermediate_channel_sizes
        num_backbone_outs = len(config.decoder_in_channels)
        encoder_input_proj_list = []
        for i in range(num_backbone_outs):
            in_channels = intermediate_channel_sizes[i]
            encoder_input_proj_list.append(
                nn.Sequential(
                    nn.Conv2d(in_channels, config.encoder_hidden_dim, kernel_size=1, bias=False),
                    nn.BatchNorm2d(config.encoder_hidden_dim),
                )
            )
        self.encoder_input_proj = nn.ModuleList(encoder_input_proj_list)
        self.encoder = DFineHybridEncoder(config=config)

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
        self.enc_bbox_head = DFineMLPPredictionHead(config.d_model, config.d_model, 4, num_layers=3)

        # init encoder output anchors and valid_mask
        if config.anchor_image_size:
            self.anchors, self.valid_mask = self.generate_anchors(dtype=self.dtype)
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
        self.decoder = DFineDecoder(config)
        decoder_input_proj = []
        in_channels = config.decoder_in_channels[-1]
        for _ in range(num_backbone_outs):
            if config.hidden_size == config.decoder_in_channels[-1]:
                decoder_input_proj.append(nn.Identity())
            else:
                conv = nn.Conv2d(in_channels, config.d_model, kernel_size=1, bias=False)
                batchnorm = nn.BatchNorm2d(config.d_model, config.batch_norm_eps)
                decoder_input_proj.append(nn.Sequential(conv, batchnorm))
        for _ in range(config.num_feature_levels - num_backbone_outs):
            if config.hidden_size == config.decoder_in_channels[-1]:
                decoder_input_proj.append(nn.Identity())
            else:
                conv = nn.Conv2d(in_channels, config.d_model, kernel_size=3, stride=2, padding=1, bias=False)
                batchnorm = nn.BatchNorm2d(config.d_model, config.batch_norm_eps)
                decoder_input_proj.append(nn.Sequential(conv, batchnorm))
        self.decoder_input_proj = nn.ModuleList(decoder_input_proj)

        self.post_init()
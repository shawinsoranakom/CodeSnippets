def __init__(self, config):
        super().__init__(config)
        self.config = config
        vision_config = config.vision_config
        text_config = config.text_config

        if config.share_cross_modal_transformer_layers:
            self.cross_modal_text_transform = nn.Linear(text_config.hidden_size, config.hidden_size)
            self.cross_modal_image_transform = nn.Linear(vision_config.hidden_size, config.hidden_size)
        else:
            self.cross_modal_text_transform = nn.ModuleList(
                [nn.Linear(text_config.hidden_size, config.hidden_size) for _ in range(config.num_hidden_layers)]
            )
            self.cross_modal_image_transform = nn.ModuleList(
                [nn.Linear(vision_config.hidden_size, config.hidden_size) for _ in range(config.num_hidden_layers)]
            )

        self.token_type_embeddings = nn.Embedding(2, config.hidden_size)

        self.vision_model = BridgeTowerVisionModel(vision_config)

        self.text_model = BridgeTowerTextModel(text_config)

        if not vision_config.share_layernorm and config.init_layernorm_from_vision_encoder:
            for ln in self.vision_model.visual.cross_modal_ln_separate:
                ln.weight.data = self.vision_model.visual.ln_post.weight.data
                ln.bias.data = self.vision_model.visual.ln_post.bias.data

        self.cross_modal_image_layers = nn.ModuleList(
            [BridgeTowerBertCrossLayer(text_config) for _ in range(config.num_hidden_layers)]
        )
        self.cross_modal_text_layers = nn.ModuleList(
            [BridgeTowerBertCrossLayer(text_config) for _ in range(config.num_hidden_layers)]
        )

        # Class token => Linear => Tanh
        self.cross_modal_image_pooler = BridgeTowerPooler(config)
        self.cross_modal_text_pooler = BridgeTowerPooler(config)

        # Initialize BridgeTower Components
        self.cross_modal_text_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.cross_modal_image_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        if config.share_link_tower_layers:
            self.cross_modal_text_link_tower = BridgeTowerLinkTower(config)
            self.cross_modal_image_link_tower = BridgeTowerLinkTower(config)
        else:
            self.cross_modal_text_link_tower = nn.ModuleList(
                [BridgeTowerLinkTower(config) for _ in range(config.num_hidden_layers - 1)]
            )
            self.cross_modal_image_link_tower = nn.ModuleList(
                [BridgeTowerLinkTower(config) for _ in range(config.num_hidden_layers - 1)]
            )

        self.post_init()
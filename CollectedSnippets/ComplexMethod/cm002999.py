def __init__(
        self,
        config: VisionTextDualEncoderConfig | None = None,
        vision_model: PreTrainedModel | None = None,
        text_model: PreTrainedModel | None = None,
    ):
        r"""
        vision_model (`PreTrainedModel`):
            The vision model to use.
        text_model (`PreTrainedModel`):
            The text model to use.
        """
        if config is None and (vision_model is None or text_model is None):
            raise ValueError("Either a configuration or an vision and a text model has to be provided")

        if config is None:
            config = VisionTextDualEncoderConfig.from_vision_text_configs(vision_model.config, text_model.config)
        else:
            if not isinstance(config, self.config_class):
                raise ValueError(f"config: {config} has to be of type {self.config_class}")

        # initialize with config
        super().__init__(config)

        if vision_model is None:
            if isinstance(config.vision_config, CLIPVisionConfig):
                vision_model = CLIPVisionModel(config.vision_config)
            else:
                vision_model = AutoModel.from_config(config.vision_config)

        if text_model is None:
            text_model = AutoModel.from_config(config.text_config)

        self.vision_model = vision_model
        self.text_model = text_model

        # make sure that the individual model's config refers to the shared config
        # so that the updates to the config will be synced
        self.config.vision_config._attn_implementation = self.vision_model.config._attn_implementation
        self.config.text_config._attn_implementation = self.text_model.config._attn_implementation
        self.vision_model.config = self.config.vision_config
        self.text_model.config = self.config.text_config

        self.vision_embed_dim = config.vision_config.hidden_size
        self.text_embed_dim = config.text_config.hidden_size
        self.projection_dim = config.projection_dim

        self.visual_projection = nn.Linear(self.vision_embed_dim, self.projection_dim, bias=False)
        self.text_projection = nn.Linear(self.text_embed_dim, self.projection_dim, bias=False)
        self.logit_scale = nn.Parameter(torch.tensor(self.config.logit_scale_init_value))

        self.post_init()
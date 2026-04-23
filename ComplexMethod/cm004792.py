def __post_init__(self, **kwargs):
        if self.readout_type not in ["ignore", "add", "project"]:
            raise ValueError("Readout_type must be one of ['ignore', 'add', 'project']")

        if self.is_hybrid:
            if isinstance(self.backbone_config, dict):
                self.backbone_config.setdefault("model_type", "bit")

            self.backbone_config, kwargs = consolidate_backbone_kwargs_to_config(
                backbone_config=self.backbone_config,
                default_config_type="bit",
                default_config_kwargs={
                    "global_padding": "same",
                    "layer_type": "bottleneck",
                    "depths": [3, 4, 9],
                    "out_features": ["stage1", "stage2", "stage3"],
                    "embedding_dynamic_padding": True,
                },
                **kwargs,
            )
            if self.readout_type != "project":
                raise ValueError("Readout type must be 'project' when using `DPT-hybrid` mode.")
        elif kwargs.get("backbone") is not None or self.backbone_config is not None:
            self.backbone_config, kwargs = consolidate_backbone_kwargs_to_config(
                backbone_config=self.backbone_config,
                **kwargs,
            )
            self.backbone_out_indices = None

        self.backbone_featmap_shape = self.backbone_featmap_shape if self.is_hybrid else None
        self.neck_ignore_stages = self.neck_ignore_stages if self.is_hybrid else []
        self.pooler_output_size = self.pooler_output_size if self.pooler_output_size else self.hidden_size
        super().__post_init__(**kwargs)
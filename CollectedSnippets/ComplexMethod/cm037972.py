def __init__(
        self,
        config: PretrainedConfig,
        quant_config: QuantizationConfig | None,
        prefix: str = "",
        model_dir: str = "",
    ) -> None:
        super().__init__()

        # n_embed or hidden_size
        hidden_size = config.n_embd if hasattr(config, "n_embd") else config.hidden_size

        # layer_idx to output the img features
        if isinstance(config.img_processor, dict):
            self.layer_idx = config.img_processor.get("layer_idx", -2)
            self.type_feature = config.img_processor.get("type_feature", "patch")
        else:
            self.layer_idx = -2
            self.type_feature = "patch"

        self.img_processor = get_navit_vision_model(layer_idx=self.layer_idx)

        pe_weight = self.img_processor.embeddings.position_embedding.weight
        L, D = pe_weight.size()
        H = int(math.sqrt(L))
        assert H**2 == L, f"position embedding size {L} is not square"
        if H % 2 != 0:
            self.img_processor_padding = nn.ReflectionPad2d((0, 1, 0, 1))
            H += 1
        image_dim_out = D
        # ((448/14)//2)**2
        self.num_img_tokens = (H // 2) ** 2
        self.base_feat_height_target = H

        self.image_dim_out = image_dim_out
        self.img_sizes = None
        self.image_attention_mask = None

        # global_gn and sub_gn for hd transform, serves as line separator
        self.use_hd_transform = True
        self.with_learnable_separator = True
        self.hd_transform_order = "sub_glb"
        self.freeze_img_processor = False
        self.crop_size = 448

        # image token compression
        self.image_token_compression_cls = "avg_pool_2d"
        self.image_token_compression = nn.AvgPool2d(kernel_size=2, stride=2)
        self.base_feat_height_reduction = 1
        self.base_feat_height_target = self.base_feat_height_target // 2

        # with_hd_transform and with_learnable_separator should have same value
        assert self.use_hd_transform == self.with_learnable_separator, (
            "use_hd_transform and with_learnable_separator should have same value"
        )
        assert self.use_hd_transform, "learnable separator is only for hd transform"
        # 1024 * 4, merge spatial to channel dimension
        self.glb_GN = nn.Parameter(
            torch.zeros([1, 1, self.image_dim_out * self.base_feat_height_reduction**2])
        )
        self.sub_GN = nn.Parameter(
            torch.zeros(
                [1, 1, 1, self.image_dim_out * self.base_feat_height_reduction**2]
            )
        )

        dim_projection = hidden_size
        depth = 2
        layers = [
            nn.Linear(
                image_dim_out * self.base_feat_height_reduction**2, dim_projection
            )
        ]
        for _ in range(1, depth):
            layers.extend([nn.GELU(), nn.Linear(dim_projection, dim_projection)])
        self.img_projection = nn.Sequential(*layers)

        self.vocab_size = config.vocab_size
        self.img_features = None

        self.use_out_place_operations = False
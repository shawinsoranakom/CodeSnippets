def __init__(self, config):
        super().__init__()

        bin_embedding_dim = config.bin_embedding_dim
        n_attractors = config.num_attractors
        self.bin_configurations = config.bin_configurations
        self.bin_centers_type = config.bin_centers_type

        # Bottleneck convolution
        bottleneck_features = config.bottleneck_features
        self.conv2 = nn.Conv2d(bottleneck_features, bottleneck_features, kernel_size=1, stride=1, padding=0)

        # Transformer classifier on the bottleneck
        self.patch_transformer = ZoeDepthPatchTransformerEncoder(config)
        # MLP classifier
        self.mlp_classifier = ZoeDepthMLPClassifier(in_features=128, out_features=2)

        # Regressor and attractor
        if self.bin_centers_type == "normed":
            Attractor = ZoeDepthAttractorLayer
        elif self.bin_centers_type == "softplus":
            Attractor = ZoeDepthAttractorLayerUnnormed
        # We have bins for each bin configuration
        # Create a map (ModuleDict) of 'name' -> seed_bin_regressor
        self.seed_bin_regressors = nn.ModuleDict(
            {
                conf["name"]: ZoeDepthSeedBinRegressor(
                    config,
                    n_bins=conf["n_bins"],
                    mlp_dim=bin_embedding_dim // 2,
                    min_depth=conf["min_depth"],
                    max_depth=conf["max_depth"],
                )
                for conf in config.bin_configurations
            }
        )

        self.seed_projector = ZoeDepthProjector(
            in_features=bottleneck_features, out_features=bin_embedding_dim, mlp_dim=bin_embedding_dim // 2
        )
        self.projectors = nn.ModuleList(
            [
                ZoeDepthProjector(
                    in_features=config.fusion_hidden_size,
                    out_features=bin_embedding_dim,
                    mlp_dim=bin_embedding_dim // 2,
                )
                for _ in range(4)
            ]
        )

        # Create a map (ModuleDict) of 'name' -> attractors (ModuleList)
        self.attractors = nn.ModuleDict(
            {
                configuration["name"]: nn.ModuleList(
                    [
                        Attractor(
                            config,
                            n_bins=n_attractors[i],
                            min_depth=configuration["min_depth"],
                            max_depth=configuration["max_depth"],
                        )
                        for i in range(len(n_attractors))
                    ]
                )
                for configuration in config.bin_configurations
            }
        )

        last_in = config.num_relative_features
        # conditional log binomial for each bin configuration
        self.conditional_log_binomial = nn.ModuleDict(
            {
                configuration["name"]: ZoeDepthConditionalLogBinomialSoftmax(
                    config,
                    last_in,
                    bin_embedding_dim,
                    configuration["n_bins"],
                    bottleneck_factor=4,
                )
                for configuration in config.bin_configurations
            }
        )
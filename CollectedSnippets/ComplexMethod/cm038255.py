def _init_possible_resolutions(
        self,
        config,
        vision_config,
    ):
        if not getattr(config, "possible_resolutions", []):
            possible_resolutions = []
            if config.anyres:
                assert config.max_num_grids > 0
                for i in range(1, config.max_num_grids + 1):
                    for j in range(1, config.max_num_grids + 1):
                        if i == 1 and j == 1 and not config.use_1x1_grid:
                            continue
                        if i * j <= config.max_num_grids:
                            possible_resolutions.append([i, j])

                possible_resolutions = [
                    [ys * vision_config.image_size, xs * vision_config.image_size]
                    for ys, xs in possible_resolutions
                ]
            return possible_resolutions
        else:
            return config.possible_resolutions
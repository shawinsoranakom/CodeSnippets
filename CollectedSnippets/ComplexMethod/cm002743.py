def __init__(self, config: HieraConfig) -> None:
        super().__init__()
        total_depth = sum(config.depths)
        # stochastic depth decay rule
        dpr = [x.item() for x in torch.linspace(0, config.drop_path_rate, total_depth, device="cpu")]
        # query strides rule
        cumulative_depths = torch.tensor(config.depths, device="cpu").cumsum(0).tolist()
        query_pool_layer = cumulative_depths[: config.num_query_pool]
        query_strides = [math.prod(config.query_stride) if i in query_pool_layer else 1 for i in range(total_depth)]

        # Transformer blocks
        self.stages = nn.ModuleList()
        hidden_size = config.embed_dim
        stage_ends = [0] + cumulative_depths
        masked_unit_area = math.prod(config.masked_unit_size)
        query_stride_area = math.prod(config.query_stride)
        for idx_stage, depth in enumerate(config.depths):
            hidden_size_output = int(config.embed_dim * config.embed_dim_multiplier**idx_stage)

            stage = HieraStage(
                config=config,
                depth=depth,
                hidden_size=hidden_size,
                hidden_size_output=hidden_size_output,
                num_heads=config.num_heads[idx_stage],
                drop_path=dpr[stage_ends[idx_stage] : stage_ends[idx_stage + 1]],
                query_stride=query_strides[stage_ends[idx_stage] : stage_ends[idx_stage + 1]],
                window_size=int(masked_unit_area * query_stride_area**-idx_stage),
                use_mask_unit_attn=config.masked_unit_attention[idx_stage],
                stage_num=idx_stage,
            )

            hidden_size = hidden_size_output
            self.stages.append(stage)

        # Setting reroll schedule
        # The first stage has to reverse everything
        # The next stage has to reverse all but the first unroll, etc.
        stage_size = [i // s for i, s in zip(config.image_size, config.patch_stride)]
        unroll_schedule = [config.query_stride] * len(config.depths[:-1])

        self.schedule = {}
        for idx_stage in range(len(config.depths)):
            self.schedule[idx_stage] = unroll_schedule, stage_size
            if idx_stage < config.num_query_pool:
                stage_size = [i // s for i, s in zip(stage_size, config.query_stride)]
                unroll_schedule = unroll_schedule[1:]

        self.gradient_checkpointing = False
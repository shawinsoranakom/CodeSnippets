def generate():
    # See csrc/quantization/machete/Readme.md, the Codegeneration for more info
    # about how this works
    SCRIPT_DIR = os.path.dirname(__file__)

    sch_common_params = dict(
        kernel_schedule=TmaMI,
        epilogue_schedule=TmaCoop,
        tile_scheduler=TileSchedulerType.StreamK,
    )

    # Stored as "condition": ((tile_shape_mn), (cluster_shape_mnk))
    default_tile_heuristic_config = {
        #### M = 257+
        "M > 256 && K <= 16384 && N <= 4096": ((128, 128), (2, 1, 1)),
        "M > 256": ((128, 256), (2, 1, 1)),
        #### M = 129-256
        "M > 128 && K <= 4096 && N <= 4096": ((128, 64), (2, 1, 1)),
        "M > 128 && K <= 8192 && N <= 8192": ((128, 128), (2, 1, 1)),
        "M > 128": ((128, 256), (2, 1, 1)),
        #### M = 65-128
        "M > 64 && K <= 4069 && N <= 4069": ((128, 32), (2, 1, 1)),
        "M > 64 && K <= 4069 && N <= 8192": ((128, 64), (2, 1, 1)),
        "M > 64 && K >= 8192 && N >= 12288": ((256, 128), (2, 1, 1)),
        "M > 64": ((128, 128), (2, 1, 1)),
        #### M = 33-64
        "M > 32 && K <= 6144 && N <= 6144": ((128, 16), (1, 1, 1)),
        "M > 32 && K >= 16384 && N >= 12288": ((256, 64), (2, 1, 1)),
        "M > 32": ((128, 64), (2, 1, 1)),
        #### M = 17-32
        "M > 16 && K <= 12288 && N <= 8192": ((128, 32), (2, 1, 1)),
        "M > 16": ((256, 32), (2, 1, 1)),
        #### M = 1-16
        "N >= 26624": ((256, 16), (1, 1, 1)),
        None: ((128, 16), (1, 1, 1)),
    }

    # For now we use the same heuristic for all types
    # Heuristic is currently tuned for H100s
    default_heuristic = [
        (cond, ScheduleConfig(*tile_config, **sch_common_params))  # type: ignore
        for cond, tile_config in default_tile_heuristic_config.items()
    ]

    def get_unique_schedules(heuristic: dict[str, ScheduleConfig]):
        # Do not use schedules = list(set(...)) because we need to make sure
        # the output list is deterministic; otherwise the generated kernel file
        # will be non-deterministic and causes ccache miss.
        schedules = []
        for _, schedule_config in heuristic:
            if schedule_config not in schedules:
                schedules.append(schedule_config)
        return schedules

    impl_configs = []

    GPTQ_kernel_type_configs = list(
        TypeConfig(
            a=a,
            b=b,
            b_group_scale=a,
            b_group_zeropoint=DataType.void,
            b_channel_scale=DataType.void,
            a_token_scale=DataType.void,
            out=a,
            accumulator=DataType.f32,
        )
        for b in (VLLMDataType.u4b8, VLLMDataType.u8b128)
        for a in (DataType.f16, DataType.bf16)
    )

    impl_configs += [
        ImplConfig(x[0], x[1], x[2])
        for x in zip(
            GPTQ_kernel_type_configs,
            itertools.repeat(get_unique_schedules(default_heuristic)),
            itertools.repeat(default_heuristic),
        )
    ]

    AWQ_kernel_type_configs = list(
        TypeConfig(
            a=a,
            b=b,
            b_group_scale=a,
            b_group_zeropoint=a,
            b_channel_scale=DataType.void,
            a_token_scale=DataType.void,
            out=a,
            accumulator=DataType.f32,
        )
        for b in (DataType.u4, DataType.u8)
        for a in (DataType.f16, DataType.bf16)
    )

    impl_configs += [
        ImplConfig(x[0], x[1], x[2])
        for x in zip(
            AWQ_kernel_type_configs,
            itertools.repeat(get_unique_schedules(default_heuristic)),
            itertools.repeat(default_heuristic),
        )
    ]

    # TODO: Support W4A8 when ready
    # # Stored as "condition": ((tile_shape_mn), (cluster_shape_mnk))
    # # TODO (LucasWilkinson): Further tuning required
    # qqq_tile_heuristic_config = {
    #     #### M = 257+
    #     # ((128, 256), (2, 1, 1)) Broken for QQQ types
    #     # TODO (LucasWilkinson): Investigate further
    #     # "M > 256 && K <= 16384 && N <= 4096": ((128, 128), (2, 1, 1)),
    #     # "M > 256": ((128, 256), (2, 1, 1)),
    #     "M > 256": ((128, 128), (2, 1, 1)),
    #     #### M = 129-256
    #     "M > 128 && K <= 4096 && N <= 4096": ((128, 64), (2, 1, 1)),
    #     "M > 128 && K <= 8192 && N <= 8192": ((128, 128), (2, 1, 1)),
    #     # ((128, 256), (2, 1, 1)) Broken for QQQ types
    #     # TODO (LucasWilkinson): Investigate further
    #     # "M > 128": ((128, 256), (2, 1, 1)),
    #     "M > 128": ((128, 128), (2, 1, 1)),
    #     #### M = 65-128
    #     "M > 64 && K <= 4069 && N <= 4069": ((128, 32), (2, 1, 1)),
    #     "M > 64 && K <= 4069 && N <= 8192": ((128, 64), (2, 1, 1)),
    #     "M > 64 && K >= 8192 && N >= 12288": ((256, 128), (2, 1, 1)),
    #     "M > 64": ((128, 128), (2, 1, 1)),
    #     #### M = 33-64
    #     "M > 32 && K <= 6144 && N <= 6144": ((128, 16), (1, 1, 1)),
    #     # Broken for QQQ types
    #     # TODO (LucasWilkinson): Investigate further
    #     #"M > 32 && K >= 16384 && N >= 12288": ((256, 64), (2, 1, 1)),
    #     "M > 32": ((128, 64), (2, 1, 1)),
    #     #### M = 17-32
    #     "M > 16 && K <= 12288 && N <= 8192": ((128, 32), (2, 1, 1)),
    #     "M > 16": ((256, 32), (2, 1, 1)),
    #     #### M = 1-16
    #     "N >= 26624": ((256, 16), (1, 1, 1)),
    #     None: ((128, 16), (1, 1, 1)),
    # }

    # # For now we use the same heuristic for all types
    # # Heuristic is currently tuned for H100s
    # qqq_heuristic = [
    #     (cond, ScheduleConfig(*tile_config,
    #                           **sch_common_params))  # type: ignore
    #     for cond, tile_config in qqq_tile_heuristic_config.items()
    # ]

    # QQQ_kernel_types = [
    #     *(TypeConfig(
    #         a=DataType.s8,
    #         b=VLLMDataType.u4b8,
    #         b_group_scale=b_group_scale,
    #         b_group_zeropoint=DataType.void,
    #         b_channel_scale=DataType.f32,
    #         a_token_scale=DataType.f32,
    #         out=DataType.f16,
    #         accumulator=DataType.s32,
    #     ) for b_group_scale in (DataType.f16, DataType.void)),
    #     *(TypeConfig(
    #         a=DataType.e4m3,
    #         b=VLLMDataType.u4b8,
    #         b_group_scale=b_group_scale,
    #         b_group_zeropoint=DataType.void,
    #         b_channel_scale=DataType.f32,
    #         a_token_scale=DataType.f32,
    #         out=DataType.f16,
    #         accumulator=DataType.f32,
    #     ) for b_group_scale in (DataType.f16, DataType.void)),
    # ]

    # impl_configs += [
    #     ImplConfig(x[0], x[1], x[2])
    #     for x in zip(QQQ_kernel_types,
    #                  itertools.repeat(get_unique_schedules(qqq_heuristic)),
    #                  itertools.repeat(qqq_heuristic))
    # ]

    output_dir = os.path.join(SCRIPT_DIR, "generated")

    # Delete the "generated" directory if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Create the "generated" directory
    os.makedirs(output_dir)

    # Render each group of configurations into separate files
    for filename, code in create_sources(impl_configs):
        filepath = os.path.join(output_dir, f"{filename}.cu")
        with open(filepath, "w") as output_file:
            output_file.write(code)
        print(f"Rendered template to {filepath}")
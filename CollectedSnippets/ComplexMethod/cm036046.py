def create_sources(impl_configs: list[ImplConfig], num_impl_files=8):
    sources = []

    sources.append(
        (
            "machete_mm_dispatch",
            mm_dispatch_template.render(impl_configs=impl_configs),
        )
    )

    prepack_types = []
    for impl_config in impl_configs:
        convert_type = (
            impl_config.types.a
            if impl_config.types.b_group_scale == DataType.void
            else impl_config.types.b_group_scale
        )
        prepack_types.append(
            PrepackTypeConfig(
                a=impl_config.types.a,
                b_num_bits=VLLMDataTypeSize[impl_config.types.b],
                convert=convert_type,
                accumulator=impl_config.types.accumulator,
            )
        )

    def prepacked_type_key(prepack_type: PrepackTypeConfig):
        # For now, we can just use the first accumulator type seen since
        # the tensor core shapes/layouts don't vary based on accumulator
        # type so we can generate less code this way
        return (prepack_type.a, prepack_type.b_num_bits, prepack_type.convert)

    unique_prepack_types = []
    prepack_types_seen = set()
    for prepack_type in prepack_types:
        key = prepacked_type_key(prepack_type)
        if key not in prepack_types_seen:
            unique_prepack_types.append(prepack_type)
            prepack_types_seen.add(key)

    sources.append(
        (
            "machete_prepack",
            prepack_dispatch_template.render(
                types=unique_prepack_types,
            ),
        )
    )

    # Split up impls across files
    num_impls = reduce(lambda x, y: x + len(y.schedules), impl_configs, 0)
    num_impls_per_file = math.ceil(num_impls / num_impl_files)

    files_impls: list[list[ImplConfig]] = [[]]

    curr_num_impls_assigned = 0
    curr_impl_in_file = 0
    curr_impl_configs = deepcopy(list(reversed(impl_configs)))

    while curr_num_impls_assigned < num_impls:
        room_left_in_file = num_impls_per_file - curr_impl_in_file
        if room_left_in_file == 0:
            files_impls.append([])
            room_left_in_file = num_impls_per_file
            curr_impl_in_file = 0

        curr_ic = curr_impl_configs[-1]
        if len(curr_ic.schedules) >= room_left_in_file:
            # Break apart the current impl config
            tmp_ic = deepcopy(curr_ic)
            tmp_ic.schedules = curr_ic.schedules[:room_left_in_file]
            curr_ic.schedules = curr_ic.schedules[room_left_in_file:]
            files_impls[-1].append(tmp_ic)
        else:
            files_impls[-1].append(curr_ic)
            curr_impl_configs.pop()
        curr_num_impls_assigned += len(files_impls[-1][-1].schedules)
        curr_impl_in_file += len(files_impls[-1][-1].schedules)

    for part, file_impls in enumerate(files_impls):
        sources.append(
            (
                f"machete_mm_impl_part{part + 1}",
                mm_impl_template.render(impl_configs=file_impls),
            )
        )

    return sources
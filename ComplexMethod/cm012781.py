def autotune_hints_to_configs(
    hints: OrderedSet[AutotuneHint],
    size_hints,
    block_size: int,
    device_props: DeviceProperties,
) -> list[Config]:
    """
    AutotuneHints can be attached to the metadata of triton kernels for providing
    suggestions about what to try for autotuning. One reason to do this is if there are
    some configs that are only useful in specific scenarios, in which case we can avoid
    wasting compile time on autotuning unless we know we are in one of those scenarios.

    Based on those hints, this function will generate a list of additional autotuning
    configs to try.
    """
    xyz_options: tuple[tuple[int, int | None, int | None], ...]
    configs: list[Config] = []
    for hint in hints:
        if hint == AutotuneHint.ONE_ELEMENT_PER_THREAD:
            if len(size_hints) == 1:
                xyz_options = ((block_size // 4, None, None),)
            elif len(size_hints) == 2:
                xyz_options = ((block_size // 4, 1, None), (1, block_size // 4, None))
            elif len(size_hints) == 3:
                xyz_options = (
                    (block_size // 4, 1, 1),
                    (1, block_size // 4, 1),
                    (1, 1, block_size // 4),
                )
            configs.extend(
                triton_config(
                    size_hints,
                    *xyz,
                    num_elements_per_warp=(
                        device_props.warp_size if device_props.warp_size else 32
                    ),
                )
                for xyz in xyz_options
            )

    return configs
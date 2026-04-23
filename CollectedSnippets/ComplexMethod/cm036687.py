def generate_params():
    is_rocm = current_platform.is_rocm()
    params = []
    device_list = ["cuda", "cpu"] if not is_rocm else ["hip", "cpu"]
    for use_mla in [True, False]:
        for device in device_list:
            backends = (
                DEVICE_MLA_BACKENDS[device]
                if use_mla
                else DEVICE_REGULAR_ATTN_BACKENDS[device]
            )
            for name in backends:
                block_sizes = DEVICE_MLA_BLOCK_SIZES[device] if use_mla else [16]
                for block_size in block_sizes:
                    params.append(
                        pytest.param(
                            device,
                            name,
                            use_mla,
                            block_size,
                            id=f"{device}_{name}_mla_{str(use_mla)[0]}_blks{block_size}",
                        )
                    )
    return params
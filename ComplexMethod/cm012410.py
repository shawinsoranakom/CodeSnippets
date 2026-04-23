def generate_kernels(
        metadata_filter: Callable[[KernelMetadata], bool],
        epilogue_args=None,
        cc: int | None = None,
    ) -> list[VendoredDenseBlockScaledGemmKernel]:
        if cc is not None and cc not in [100, 101, 103]:
            return []
        if epilogue_args is not None:
            return []

        design_params = {
            "use_2cta_mma": [True],
            "tile_shape": [
                (M, N, 256) for M in [128, 256] for N in [64, 128, 192, 256]
            ],
            "cluster_shape": [(M, N, 1) for M in [1, 2, 4] for N in [1, 2, 4]],
            "use_tma_store": [True],
        }

        param_names = list(design_params.keys())
        param_values = [design_params[name] for name in param_names]

        kernel_list = []

        for (
            operands
        ) in VendoredDenseBlockScaledGemmKernel._metadata_operand_combinations():
            # pyrefly: ignore[no-matching-overload]
            for values in itertools.product(*param_values):
                design = Sm100DesignMetadata(**dict(zip(param_names, values)))

                kernel_name = (
                    "inductor_vendored.DenseBlockScaledGemmKernel_sm100_"
                    "{layout}_A{A}_B{B}_out{out}_SFA{SFA}_SFB{SFB}_"
                    "acc{acc}_scale{scale_mode}_swizzle{scale_swizzle}_"
                    "{num_cta}cta_cluster{cluster}_tile{tile}"
                    "{_tma_store}"
                ).format(
                    layout=strides_to_layout_string(
                        operands.A.stride,
                        operands.B.stride,
                        operands.out.stride,
                    ),
                    A=operands.A.dtype,
                    B=operands.B.dtype,
                    out=operands.out.dtype,
                    SFA=operands.A.scale.dtype,
                    SFB=operands.B.scale.dtype,
                    acc=operands.accumulator_type,
                    scale_mode=operands.A.mode,
                    scale_swizzle=operands.A.swizzle,
                    num_cta="2" if design.use_2cta_mma else "1",
                    cluster=tuple_to_string(design.cluster_shape),
                    tile=tuple_to_string(design.tile_shape),
                    _tma_store="_tma_store" if design.use_tma_store else "",
                )

                metadata = KernelMetadata(
                    operands=operands,
                    design=design,
                    kernel_name=kernel_name,
                    kernel_class=VendoredDenseBlockScaledGemmKernel,
                    min_cc=100,
                    epilogue=None,
                )

                if VendoredDenseBlockScaledGemmKernel._valid_metadata(metadata):
                    if metadata_filter is None or metadata_filter(metadata):
                        kernel_list.append(VendoredDenseBlockScaledGemmKernel(metadata))

        log.debug(
            "Generated %d DenseBlockScaledGemmKernel configurations",
            len(kernel_list),
        )
        return kernel_list
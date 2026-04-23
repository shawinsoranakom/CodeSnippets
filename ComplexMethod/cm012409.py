def _valid_metadata(metadata: KernelMetadata) -> bool:
        scale_vec = metadata.operands.A.mode

        if len(scale_vec) > 1:
            for i in range(len(scale_vec) - 1):
                if scale_vec[i] != 1:
                    return False

        sf_vec_size = scale_vec[-1]
        if not VendoredDenseBlockScaledGemmKernel._valid_operands(
            metadata.operands, sf_vec_size
        ):
            return False

        design = metadata.design
        if not isinstance(design, Sm100DesignMetadata):
            return False

        cm, cn, _ = design.cluster_shape
        if cm <= 0 or cn <= 0:
            return False
        if cm * cn > 16:
            return False
        if cm & (cm - 1) != 0 or cn & (cn - 1) != 0:
            return False
        # SF multicast constraint: cluster dims <=4
        if cm > 4 or cn > 4:
            return False

        tile_m, tile_n, _ = design.tile_shape
        if tile_m not in [128, 256]:
            return False
        if tile_n not in [64, 128, 192, 256]:
            return False
        use_2cta = tile_m == 256
        if use_2cta and cm % 2 != 0:
            return False

        if metadata.epilogue is not None:
            return False

        return True
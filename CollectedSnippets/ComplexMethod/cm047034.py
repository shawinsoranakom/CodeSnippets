def backward(ctx, dY):
        dY = dY.contiguous()
        X, W, m_sizes, gather_indices = ctx.saved_tensors
        topk = ctx.topk
        permute_x = ctx.permute_x
        permute_y = ctx.permute_y
        fuse_mul_post = ctx.fuse_mul_post
        kernel_config_bwd_dX = ctx.kernel_config_bwd_dX
        kernel_config_bwd_dW = ctx.kernel_config_bwd_dW
        autotune = ctx.autotune
        dX_only = ctx.dX_only
        dW_only = ctx.dW_only

        if not autotune:
            if not dW_only:
                assert (
                    kernel_config_bwd_dX is not None
                ), "kernel_config_bwd_dX must be provided if autotune is False"
            if not dX_only:
                assert (
                    kernel_config_bwd_dW is not None
                ), "kernel_config_bwd_dW must be provided if autotune is False"

        assert (
            not fuse_mul_post
        ), "fused_mul should only be used for inference, not for training"

        if not dX_only:
            bwd_dW_config = {}

            if kernel_config_bwd_dW is not None:
                bwd_dW_config["use_tma_load_dy"] = kernel_config_bwd_dW.use_tma_load_dy
                bwd_dW_config["use_tma_load_x"] = kernel_config_bwd_dW.use_tma_load_x
                bwd_dW_config["use_tma_store"] = kernel_config_bwd_dW.use_tma_store
                bwd_dW_config["BLOCK_SIZE_M"] = kernel_config_bwd_dW.BLOCK_SIZE_M
                bwd_dW_config["BLOCK_SIZE_N"] = kernel_config_bwd_dW.BLOCK_SIZE_N
                bwd_dW_config["BLOCK_SIZE_K"] = kernel_config_bwd_dW.BLOCK_SIZE_K
                bwd_dW_config["num_warps"] = kernel_config_bwd_dW.num_warps
                bwd_dW_config["num_stages"] = kernel_config_bwd_dW.num_stages

            dW = grouped_gemm_dW(
                X = X,
                dY = dY,
                m_sizes = m_sizes,
                gather_indices = gather_indices,
                topk = topk,
                permute_x = permute_x,
                permute_y = permute_y,
                # Autotune -- this will override the manual kernel config if true
                autotune = autotune,
                # Manual kernel config
                **bwd_dW_config,
            )
        else:
            dW = None

        if not dW_only:
            bwd_dX_config = {}
            if kernel_config_bwd_dX is not None:
                bwd_dX_config["use_tma_load_dy"] = kernel_config_bwd_dX.use_tma_load_dy
                bwd_dX_config["use_tma_load_w"] = kernel_config_bwd_dX.use_tma_load_w
                bwd_dX_config["use_tma_store"] = kernel_config_bwd_dX.use_tma_store
                bwd_dX_config["BLOCK_SIZE_M"] = kernel_config_bwd_dX.BLOCK_SIZE_M
                bwd_dX_config["BLOCK_SIZE_N"] = kernel_config_bwd_dX.BLOCK_SIZE_N
                bwd_dX_config["BLOCK_SIZE_K"] = kernel_config_bwd_dX.BLOCK_SIZE_K
                bwd_dX_config["num_warps"] = kernel_config_bwd_dX.num_warps
                bwd_dX_config["num_stages"] = kernel_config_bwd_dX.num_stages

            dX = grouped_gemm_dX(
                dY = dY,
                W = W,
                m_sizes = m_sizes,
                gather_indices = gather_indices,
                topk = topk,
                permute_x = permute_x,
                permute_y = permute_y,
                # Autotune -- this will override the manual kernel config if true
                autotune = autotune,
                # Manual kernel config
                **bwd_dX_config,
            )

            if topk > 1 and permute_x:
                dX = dX.view(X.shape[0], topk, -1).sum(dim = 1)
        else:
            dX = None

        return (
            dX,
            dW,
            None,  # m_sizes
            None,  # gather_indices
            None,  # topk
            None,  # permute_x
            None,  # permute_y
            None,  # topk_weights
            None,  # fuse_mul_post
            None,  # kernel_config_fwd
            None,  # kernel_config_bwd_dX
            None,  # kernel_config_bwd_dW
            None,  # autotune
            None,  # dX_only
            None,  # dW_only
        )
def check_valid_config_bwd_dX(
    permute_x,
    permute_y,
    use_tma_load_dY,
    use_tma_load_w,
    use_tma_store,
    fuse_mul_post,
    is_first_gemm,
):
    """
    Check if the configuration is valid for the backward pass of dW.
    """
    is_second_gemm = not is_first_gemm
    if fuse_mul_post:
        assert False, "Cannot fuse_mul is not supported for backward pass"
    if is_second_gemm and permute_y and use_tma_load_dY:
        assert False, "Cannot use TMA load and permute Y for the second grouped GEMM"
    if use_tma_store and permute_x and is_first_gemm:
        assert False, "Cannot use TMA store and permute X for the first grouped GEMM"
def _should_generate_scaled_grouped_mm_configs() -> bool:
    # Minimum requirements:
    # - PyTorch 2.9+ (scaled_grouped_mm introduced)
    # - CUDA: compute capability exactly 9.0 (SM90) or 10.0 (SM100) and CUDA 12.8+
    # - ROCm: MI300+ (gfx94x) grouped GEMM support
    if TorchVersion(torch.__version__) < "2.9" or not hasattr(
        torch.nn.functional, "scaled_grouped_mm"
    ):
        return False
    if not torch.cuda.is_available():
        return False

    if torch.version.hip is not None:
        return bool(PLATFORM_SUPPORTS_FP8_GROUPED_GEMM)

    # CUDA build: some scale modes require CUDA 12.8+ (see `aten/src/ATen/cuda/CUDABlas.cpp:get_scale_mode`).
    if TorchVersion(torch.version.cuda or "0.0") < "12.8":
        return False

    return bool(IS_SM90) or bool(IS_SM100)
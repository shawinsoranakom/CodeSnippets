def detect_hardware() -> DeviceType:
    """
    Detect the best available compute device and set the module-level DEVICE global.

    Should be called exactly once during FastAPI lifespan startup.
    Safe to call multiple times (idempotent).

    Detection order:
      1. CUDA  (NVIDIA GPU, requires torch)
      2. MLX   (Apple Silicon via MLX framework)
      3. CPU   (fallback)
    """
    global DEVICE, CHAT_ONLY, IS_ROCM
    CHAT_ONLY = True  # reset -- only CUDA/ROCm sets it to False
    IS_ROCM = False

    # --- CUDA / ROCm: try PyTorch ---
    if _has_torch():
        import torch

        if torch.cuda.is_available():
            DEVICE = DeviceType.CUDA
            CHAT_ONLY = False
            device_name = torch.cuda.get_device_properties(0).name

            # Distinguish AMD ROCm (HIP) from NVIDIA CUDA for display purposes.
            # DeviceType stays CUDA since torch.cuda.* works on ROCm via HIP.
            if getattr(torch.version, "hip", None) is not None:
                IS_ROCM = True
                print(
                    f"Hardware detected: ROCm (HIP {torch.version.hip}) -- {device_name}"
                )
            else:
                print(f"Hardware detected: CUDA -- {device_name}")
            return DEVICE

    # --- XPU: Intel GPU ---
    if _has_torch():
        import torch

        if hasattr(torch, "xpu") and torch.xpu.is_available():
            DEVICE = DeviceType.XPU
            CHAT_ONLY = False
            device_name = torch.xpu.get_device_name(0)
            print(f"Hardware detected: XPU — {device_name}")
            return DEVICE

    # --- MLX: Apple Silicon ---
    if is_apple_silicon() and _has_mlx():
        DEVICE = DeviceType.MLX
        chip = platform.processor() or platform.machine()
        print(f"Hardware detected: MLX — Apple Silicon ({chip})")
        return DEVICE

    # --- Fallback ---
    DEVICE = DeviceType.CPU
    print("Hardware detected: CPU (no GPU backend available)")
    return DEVICE
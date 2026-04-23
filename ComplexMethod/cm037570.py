def __init__(self, approximate: str = "none"):
        super().__init__()
        self.approximate = approximate
        if approximate not in ("none", "tanh"):
            raise ValueError(f"Unknown approximate mode: {approximate}")
        if (
            current_platform.is_cuda_alike()
            or current_platform.is_cpu()
            or current_platform.is_xpu()
        ):
            if approximate == "none":
                self.op = torch.ops._C.gelu_and_mul
            elif approximate == "tanh":
                self.op = torch.ops._C.gelu_tanh_and_mul
        if current_platform.is_rocm() and approximate == "tanh":
            logger.warning_once(
                "[ROCm] PyTorch's native GELU with tanh approximation is unstable "
                "with torch.compile. For native implementation, fallback to 'none' "
                "approximation. The custom kernel implementation is unaffected."
            )
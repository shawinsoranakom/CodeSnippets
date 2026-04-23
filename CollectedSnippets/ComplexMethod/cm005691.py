def is_torch_bf16_gpu_available() -> bool:
    if not is_torch_available():
        return False

    import torch

    if torch.cuda.is_available():
        return torch.cuda.is_bf16_supported()
    if is_torch_xpu_available():
        return torch.xpu.is_bf16_supported()
    if is_torch_hpu_available():
        return True
    if is_torch_npu_available() and hasattr(torch, "npu"):
        return torch.npu.is_bf16_supported()
    if is_torch_mps_available():
        # Note: Emulated in software by Metal using fp32 for hardware without native support (like M1/M2)
        return torch.backends.mps.is_macos_or_newer(14, 0)
    if is_torch_musa_available() and hasattr(torch, "musa"):
        return torch.musa.is_bf16_supported()
    if is_torch_mlu_available() and hasattr(torch, "mlu"):
        return torch.mlu.is_bf16_supported()
    if is_torch_neuron_available() and hasattr(torch, "neuron"):
        return torch.neuron.is_bf16_supported()
    return False
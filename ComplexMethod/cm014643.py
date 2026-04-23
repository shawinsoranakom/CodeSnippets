def _categorize(name: str) -> str:
    """Assign a category based on the symbol's namespace."""
    if name.startswith("torch::nn::functional::"):
        return "torch::nn::functional"
    if name.startswith("torch::nn::init::"):
        return "torch::nn::init"
    if name.startswith("torch::nn::utils::"):
        return "torch::nn::utils"
    if name.startswith("torch::nn::"):
        # Distinguish modules from other nn symbols
        short = name.split("::")[-1]
        if short[0].isupper():
            return "torch::nn (modules)"
        return "torch::nn"
    if name.startswith("torch::optim::"):
        return "torch::optim"
    if name.startswith("torch::data::"):
        return "torch::data"
    if name.startswith("torch::autograd::"):
        return "torch::autograd"
    if name.startswith("torch::serialize::") or name in ("torch::save", "torch::load"):
        return "torch::serialize"
    if name.startswith("torch::stable::"):
        return "torch::stable"
    if name.startswith("torch::fft::"):
        return "torch::fft"
    if name.startswith("torch::special::"):
        return "torch::special"
    if name.startswith(("torch::cuda::", "torch::mps::", "torch::xpu::")):
        return "torch (device)"
    if name.startswith("torch::"):
        return "torch (core)"
    if name.startswith("c10::cuda::"):
        return "c10::cuda"
    if name.startswith("c10::xpu::"):
        return "c10::xpu"
    if name.startswith("c10::"):
        return "c10"
    if name.startswith("at::cuda::"):
        return "at::cuda"
    if name.startswith("at::"):
        return "at"
    return "other"
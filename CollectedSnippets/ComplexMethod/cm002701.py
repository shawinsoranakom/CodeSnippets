def set_seed(seed: int, deterministic: bool = False):
    """
    Helper function for reproducible behavior to set the seed in `random`, `numpy`, `torch` (if installed).

    Args:
        seed (`int`):
            The seed to set.
        deterministic (`bool`, *optional*, defaults to `False`):
            Whether to use deterministic algorithms where available. Can slow down training.
    """
    random.seed(seed)
    np.random.seed(seed)
    if is_torch_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # ^^ safe to call this function even if cuda is not available
        if deterministic:
            torch.use_deterministic_algorithms(True)
    if is_torch_mlu_available():
        torch.mlu.manual_seed_all(seed)
    if is_torch_musa_available():
        torch.musa.manual_seed_all(seed)
    if is_torch_npu_available():
        torch.npu.manual_seed_all(seed)
    if is_torch_hpu_available():
        torch.hpu.manual_seed_all(seed)
    if is_torch_xpu_available():
        torch.xpu.manual_seed_all(seed)
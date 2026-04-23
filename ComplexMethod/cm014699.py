def _bf16_state_init_hook(optimizer, args, kwargs):
    """Step pre-hook that initializes Adam/AdamW states in bfloat16.

    Pre-populates optimizer state before Adam's lazy initialization so that
    ``_init_group`` finds non-empty state and skips its own fp32 allocation.
    The fused CUDA kernel then dispatches to its mixed-precision path.
    """
    for group in optimizer.param_groups:
        for p in group["params"]:
            if p.grad is None:
                continue
            state = optimizer.state[p]
            if len(state) == 0:
                state["step"] = (
                    torch.zeros((), dtype=torch.float32, device=p.device)
                    if group.get("capturable") or group.get("fused")
                    else torch.tensor(0.0, dtype=torch.float32)
                )
                state["exp_avg"] = torch.zeros_like(
                    p, dtype=torch.bfloat16, memory_format=torch.preserve_format
                )
                state["exp_avg_sq"] = torch.zeros_like(
                    p, dtype=torch.bfloat16, memory_format=torch.preserve_format
                )
                if group.get("amsgrad"):
                    state["max_exp_avg_sq"] = torch.zeros_like(
                        p,
                        dtype=torch.bfloat16,
                        memory_format=torch.preserve_format,
                    )
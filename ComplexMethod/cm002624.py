def _get_wsd_scheduler_lambda(
    current_step: int,
    *,
    num_warmup_steps: int,
    num_stable_steps: int,
    num_decay_steps: int,
    warmup_type: str,
    decay_type: str,
    min_lr_ratio: float,
    num_cycles: float,
):
    if current_step < num_warmup_steps:
        progress = float(current_step) / float(max(1, num_warmup_steps))
        if warmup_type == "linear":
            factor = progress
        elif warmup_type == "cosine":
            factor = 0.5 * (1.0 - math.cos(math.pi * progress))
        elif warmup_type == "1-sqrt":
            factor = 1.0 - math.sqrt(1.0 - progress)
        factor = factor * (1.0 - min_lr_ratio) + min_lr_ratio
        return max(0.0, factor)

    if current_step < num_warmup_steps + num_stable_steps:
        return 1.0

    if current_step < num_warmup_steps + num_stable_steps + num_decay_steps:
        progress = float(current_step - num_warmup_steps - num_stable_steps) / float(max(1, num_decay_steps))
        if decay_type == "linear":
            factor = 1.0 - progress
        elif decay_type == "cosine":
            factor = 0.5 * (1.0 + math.cos(math.pi * float(num_cycles) * 2.0 * progress))
        elif decay_type == "1-sqrt":
            factor = 1.0 - math.sqrt(progress)
        factor = factor * (1.0 - min_lr_ratio) + min_lr_ratio
        return max(0.0, factor)
    return min_lr_ratio
def get_wsd_schedule(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_decay_steps: int,
    num_training_steps: int | None = None,
    num_stable_steps: int | None = None,
    warmup_type: str = "linear",
    decay_type: str = "cosine",
    min_lr_ratio: float = 0,
    num_cycles: float = 0.5,
    last_epoch: int = -1,
):
    """
    Create a schedule with a learning rate that has three stages:
    1. warmup: increase from min_lr_ratio times the initial learning rate to the initial learning rate following a warmup_type.
    2. stable: constant learning rate.
    3. decay: decrease from the initial learning rate to min_lr_ratio times the initial learning rate following a decay_type.

    Args:
        optimizer ([`~torch.optim.Optimizer`]):
            The optimizer for which to schedule the learning rate.
        num_warmup_steps (`int`):
            The number of steps for the warmup phase.
        num_decay_steps (`int`):
            The number of steps for the decay phase.
        num_training_steps (`int`, *optional*):
            The total number of training steps. This is the sum of the warmup, stable and decay steps. If `num_stable_steps` is not provided, the stable phase will be `num_training_steps - num_warmup_steps - num_decay_steps`.
        num_stable_steps (`int`, *optional*):
            The number of steps for the stable phase. Please ensure that `num_warmup_steps + num_stable_steps + num_decay_steps` equals `num_training_steps`, otherwise the other steps will default to the minimum learning rate.
        warmup_type (`str`, *optional*, defaults to "linear"):
            The type of warmup to use. Can be 'linear', 'cosine' or '1-sqrt'.
        decay_type (`str`, *optional*, defaults to "cosine"):
            The type of decay to use. Can be 'linear', 'cosine' or '1-sqrt'.
        min_lr_ratio (`float`, *optional*, defaults to 0):
            The minimum learning rate as a ratio of the initial learning rate.
        num_cycles (`float`, *optional*, defaults to 0.5):
            The number of waves in the cosine schedule (the defaults is to just decrease from the max value to 0
            following a half-cosine).
        last_epoch (`int`, *optional*, defaults to -1):
            The index of the last epoch when resuming training.

    Return:
        `torch.optim.lr_scheduler.LambdaLR` with the appropriate schedule.
    """

    if num_training_steps is None and num_stable_steps is None:
        raise ValueError("Either num_training_steps or num_stable_steps must be specified.")

    if num_training_steps is not None and num_stable_steps is not None:
        warnings.warn("Both num_training_steps and num_stable_steps are specified. num_stable_steps will be used.")

    if warmup_type not in ["linear", "cosine", "1-sqrt"]:
        raise ValueError(f"Unknown warmup type: {warmup_type}, expected 'linear', 'cosine' or '1-sqrt'")

    if decay_type not in ["linear", "cosine", "1-sqrt"]:
        raise ValueError(f"Unknown decay type: {decay_type}, expected 'linear', 'cosine' or '1-sqrt'")

    if num_stable_steps is None:
        num_stable_steps = num_training_steps - num_warmup_steps - num_decay_steps

    lr_lambda = partial(
        _get_wsd_scheduler_lambda,
        num_warmup_steps=num_warmup_steps,
        num_stable_steps=num_stable_steps,
        num_decay_steps=num_decay_steps,
        warmup_type=warmup_type,
        decay_type=decay_type,
        min_lr_ratio=min_lr_ratio,
        num_cycles=num_cycles,
    )
    return LambdaLR(optimizer, lr_lambda, last_epoch)
def get_scheduler(
    name: str | SchedulerType,
    optimizer: Optimizer,
    num_warmup_steps: int | None = None,
    num_training_steps: int | None = None,
    scheduler_specific_kwargs: dict | None = None,
):
    """
    Unified API to get any scheduler from its name.

    Args:
        name (`str` or `SchedulerType`):
            The name of the scheduler to use.
        optimizer (`torch.optim.Optimizer`):
            The optimizer that will be used during training.
        num_warmup_steps (`int`, *optional*):
            The number of warmup steps to do. This is not required by all schedulers (hence the argument being
            optional), the function will raise an error if it's unset and the scheduler type requires it.
        num_training_steps (`int``, *optional*):
            The number of training steps to do. This is not required by all schedulers (hence the argument being
            optional), the function will raise an error if it's unset and the scheduler type requires it.
        scheduler_specific_kwargs (`dict`, *optional*):
            Extra parameters for schedulers such as cosine with restarts. Mismatched scheduler types and scheduler
            parameters will cause the scheduler function to raise a TypeError.
    """
    name = SchedulerType(name)
    schedule_func = TYPE_TO_SCHEDULER_FUNCTION[name]

    # If a `LayerWiseDummyOptimizer` is passed we extract the optimizer dict and
    # recursively call `get_scheduler` to get the proper schedulers on each parameter
    if optimizer is not None and isinstance(optimizer, LayerWiseDummyOptimizer):
        optimizer_dict = optimizer.optimizer_dict
        scheduler_dict = {}

        for param in optimizer_dict:
            scheduler_dict[param] = get_scheduler(
                name,
                optimizer=optimizer_dict[param],
                num_warmup_steps=num_warmup_steps,
                num_training_steps=num_training_steps,
                scheduler_specific_kwargs=scheduler_specific_kwargs,
            )

        def scheduler_hook(param):
            # Since the optimizer hook has been already attached we only need to
            # attach the scheduler hook, the gradients have been zeroed here
            scheduler_dict[param].step()

        for param in optimizer_dict:
            if param.requires_grad:
                param.register_post_accumulate_grad_hook(scheduler_hook)

        return LayerWiseDummyScheduler(optimizer_dict=optimizer_dict, lr=optimizer.defaults["lr"])

    if name == SchedulerType.CONSTANT:
        return schedule_func(optimizer)

    if scheduler_specific_kwargs is None:
        scheduler_specific_kwargs = {}

    if name == SchedulerType.REDUCE_ON_PLATEAU:
        return schedule_func(optimizer, **scheduler_specific_kwargs)

    if name == SchedulerType.GREEDY:
        return schedule_func(optimizer, **scheduler_specific_kwargs)

    # All other schedulers require `num_warmup_steps`
    if num_warmup_steps is None:
        raise ValueError(f"{name} requires `num_warmup_steps`, please provide that argument.")

    if name == SchedulerType.CONSTANT_WITH_WARMUP:
        return schedule_func(optimizer, num_warmup_steps=num_warmup_steps)

    if name == SchedulerType.INVERSE_SQRT:
        return schedule_func(optimizer, num_warmup_steps=num_warmup_steps, **scheduler_specific_kwargs)

    # wsd scheduler requires either num_training_steps or num_stable_steps
    if name == SchedulerType.WARMUP_STABLE_DECAY:
        return schedule_func(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps,
            **scheduler_specific_kwargs,
        )

    # All other schedulers require `num_training_steps`
    if num_training_steps is None:
        raise ValueError(f"{name} requires `num_training_steps`, please provide that argument.")

    return schedule_func(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps,
        **scheduler_specific_kwargs,
    )
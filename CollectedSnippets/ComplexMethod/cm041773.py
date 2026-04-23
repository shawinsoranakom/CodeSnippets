def create_custom_scheduler(
    training_args: "TrainingArguments",
    num_training_steps: int,
    optimizer: Optional["torch.optim.Optimizer"] = None,
) -> None:
    if training_args.lr_scheduler_type == "warmup_stable_decay":
        num_warmup_steps = training_args.get_warmup_steps(num_training_steps)
        remaining_steps = num_training_steps - num_warmup_steps
        num_stable_steps = remaining_steps // 3  # use 1/3 for stable by default
        num_decay_steps = remaining_steps - num_stable_steps
        scheduler_kwargs = training_args.lr_scheduler_kwargs or {}
        default_kwargs = {
            "num_stable_steps": num_stable_steps,
            "num_decay_steps": num_decay_steps,
        }
        for key, value in default_kwargs.items():
            if key not in scheduler_kwargs:
                scheduler_kwargs[key] = value

        training_args.lr_scheduler_kwargs = scheduler_kwargs

    if optimizer is not None and isinstance(optimizer, DummyOptimizer):
        optimizer_dict = optimizer.optimizer_dict
        scheduler_dict: dict[torch.nn.Parameter, torch.optim.lr_scheduler.LRScheduler] = {}

        for param in optimizer_dict.keys():
            scheduler_dict[param] = get_scheduler(
                training_args.lr_scheduler_type,
                optimizer=optimizer_dict[param],
                num_warmup_steps=training_args.get_warmup_steps(num_training_steps),
                num_training_steps=num_training_steps,
                scheduler_specific_kwargs=training_args.lr_scheduler_kwargs,
            )

        def scheduler_hook(param: "torch.nn.Parameter"):
            scheduler_dict[param].step()

        for param in optimizer_dict.keys():
            param.register_post_accumulate_grad_hook(scheduler_hook)
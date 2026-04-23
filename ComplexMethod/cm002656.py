def extract_hyperparameters_from_trainer(trainer):
    hyperparameters = {k: getattr(trainer.args, k) for k in _TRAINING_ARGS_KEYS}

    if trainer.args.parallel_mode not in [ParallelMode.NOT_PARALLEL, ParallelMode.NOT_DISTRIBUTED]:
        hyperparameters["distributed_type"] = (
            "multi-GPU" if trainer.args.parallel_mode == ParallelMode.DISTRIBUTED else trainer.args.parallel_mode.value
        )
    if trainer.args.world_size > 1:
        hyperparameters["num_devices"] = trainer.args.world_size
    if trainer.args.gradient_accumulation_steps > 1:
        hyperparameters["gradient_accumulation_steps"] = trainer.args.gradient_accumulation_steps

    total_train_batch_size = (
        trainer.args.train_batch_size * trainer.args.world_size * trainer.args.gradient_accumulation_steps
    )
    if total_train_batch_size != hyperparameters["train_batch_size"]:
        hyperparameters["total_train_batch_size"] = total_train_batch_size
    total_eval_batch_size = trainer.args.eval_batch_size * trainer.args.world_size
    if total_eval_batch_size != hyperparameters["eval_batch_size"]:
        hyperparameters["total_eval_batch_size"] = total_eval_batch_size

    if trainer.args.optim:
        optimizer_name = trainer.args.optim
        optimizer_args = trainer.args.optim_args if trainer.args.optim_args else "No additional optimizer arguments"

        if "adam" in optimizer_name.lower():
            hyperparameters["optimizer"] = (
                f"Use {optimizer_name} with betas=({trainer.args.adam_beta1},{trainer.args.adam_beta2}) and"
                f" epsilon={trainer.args.adam_epsilon} and optimizer_args={optimizer_args}"
            )
        else:
            hyperparameters["optimizer"] = f"Use {optimizer_name} and the args are:\n{optimizer_args}"

    hyperparameters["lr_scheduler_type"] = trainer.args.lr_scheduler_type.value
    if trainer.args.warmup_steps != 0.0:
        hyperparameters["lr_scheduler_warmup_steps"] = trainer.args.warmup_steps
    if trainer.args.max_steps != -1:
        hyperparameters["training_steps"] = trainer.args.max_steps
    else:
        hyperparameters["num_epochs"] = trainer.args.num_train_epochs

    if trainer.args.fp16:
        hyperparameters["mixed_precision_training"] = "Native AMP"

    if trainer.args.label_smoothing_factor != 0.0:
        hyperparameters["label_smoothing_factor"] = trainer.args.label_smoothing_factor

    return hyperparameters
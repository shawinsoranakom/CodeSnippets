def _build_audio_training_args(self, training_args, output_dir, *, extra_args = None):
        """Build training args dict for audio branches.

        Constructs the common config (batch size, lr, warmup, fp16/bf16, etc.)
        and applies per-branch overrides via extra_args.
        """
        batch_size = training_args.get("batch_size", 2)
        gradient_accumulation_steps = training_args.get(
            "gradient_accumulation_steps", 4
        )
        warmup_steps_val = training_args.get("warmup_steps", 5)
        max_steps_val = training_args.get("max_steps", 0)
        learning_rate = training_args.get("learning_rate", 2e-4)
        weight_decay = training_args.get("weight_decay", 0.001)
        lr_scheduler_type = training_args.get("lr_scheduler_type", "linear")
        random_seed = training_args.get("random_seed", 3407)
        optim_value = training_args.get("optim", "adamw_8bit")

        config = {
            "per_device_train_batch_size": batch_size,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "warmup_steps": warmup_steps_val if warmup_steps_val is not None else 5,
            "learning_rate": learning_rate,
            "fp16": not is_bfloat16_supported(),
            "bf16": is_bfloat16_supported(),
            "logging_steps": 1,
            "optim": optim_value,
            "weight_decay": weight_decay,
            "lr_scheduler_type": lr_scheduler_type,
            "seed": random_seed,
            "output_dir": output_dir,
            "report_to": _build_report_targets(training_args),
        }

        if training_args.get("enable_tensorboard", False):
            config["logging_dir"] = str(
                resolve_tensorboard_dir(training_args.get("tensorboard_dir"))
            )

        # max_steps vs epochs
        if max_steps_val and max_steps_val > 0:
            config["max_steps"] = max_steps_val
        else:
            config["num_train_epochs"] = training_args.get("num_epochs", 3)

        # save_steps
        save_steps_val = training_args.get("save_steps", 0)
        if save_steps_val and save_steps_val > 0:
            config["save_steps"] = save_steps_val
            config["save_strategy"] = "steps"

        # Apply per-branch overrides
        if extra_args:
            config.update(extra_args)

        return config
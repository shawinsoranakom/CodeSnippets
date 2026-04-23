def _inner_training_loop(
        self,
        batch_size: int | None = None,
        args: TrainingArguments | None = None,
        resume_from_checkpoint: str | None = None,
        trial: "optuna.Trial | dict[str, Any] | None" = None,
        ignore_keys_for_eval: list[str] | None = None,
    ) -> TrainOutput:
        """Run the actual training loop: forward, backward, optimizer step, logging, and checkpointing."""
        # reset everything
        self.accelerator.free_memory()
        if args.auto_find_batch_size:
            self._update_auto_batch_size(batch_size)
        # Data loader and number of training steps
        train_dataloader = self.get_train_dataloader()
        if self.is_fsdp_xla_v2_enabled:
            train_dataloader = tpu_spmd_dataloader(train_dataloader)

        # Setting up training control variables:
        (
            num_train_epochs,
            num_update_steps_per_epoch,
            num_examples,
            num_train_samples,
            total_train_batch_size,
            steps_in_epoch,
            max_steps,
        ) = self.set_initial_training_values(args, train_dataloader)

        epochs_trained, steps_trained_in_current_epoch = self._init_training_state(
            max_steps, num_update_steps_per_epoch, num_train_epochs, resume_from_checkpoint, trial
        )
        model, train_dataloader = self._prepare_for_training(max_steps, train_dataloader, resume_from_checkpoint)

        # Train!
        logger.info("***** Running training *****")
        logger.info(f"  Num examples = {num_examples:,}")
        logger.info(f"  Num Epochs = {num_train_epochs:,}")
        logger.info(f"  Num update steps per epoch = {num_update_steps_per_epoch:,}")
        logger.info(f"  Instantaneous batch size per device = {self.args.per_device_train_batch_size:,}")
        if self.args.per_device_train_batch_size != self._train_batch_size:
            logger.info(f"  Training with DataParallel so batch size has been adjusted to: {self._train_batch_size:,}")
        logger.info(f"  Total train batch size (w. parallel, distributed & accumulation) = {total_train_batch_size:,}")
        logger.info(f"  Gradient Accumulation steps = {args.gradient_accumulation_steps}")
        logger.info(f"  Total optimization steps = {max_steps:,}")
        logger.info(f"  Number of trainable parameters = {get_model_param_count(model, trainable_only=True):,}")

        if resume_from_checkpoint is not None:
            logger.info(
                f"  Resuming training from checkpoint with epoch {epochs_trained} and global step {self.state.global_step}"
            )
            if not self.args.ignore_data_skip:
                logger.info(
                    f"  Fast-forwarding the dataloader past {epochs_trained} epochs and"
                    f" {steps_trained_in_current_epoch} batches to resume from the exact training state."
                )

        start_time = time.time()
        # needed to calculate tokens/s
        self._initial_num_input_tokens_seen = self.state.num_input_tokens_seen
        # Logging state: _tr_loss accumulates on-device between logging steps (avoiding costly .item() syncs
        # on TPUs), then gets drained into _total_loss_scalar at each logging step.
        self._tr_loss = torch.tensor(0.0, device=args.device)
        self._total_loss_scalar = 0.0
        self._globalstep_last_logged = self.state.global_step

        model.zero_grad()

        self.control = self.callback_handler.on_train_begin(args, self.state, self.control)

        if args.eval_on_start:
            self._evaluate(trial, ignore_keys_for_eval, skip_scheduler=True)

        for epoch in range(epochs_trained, num_train_epochs):
            self.control = self.callback_handler.on_epoch_begin(self.args, self.state, self.control)
            self._run_epoch(
                model=model,
                epoch=epoch,
                train_dataloader=train_dataloader,
                steps_in_epoch=steps_in_epoch,
                num_update_steps_per_epoch=num_update_steps_per_epoch,
                trial=trial,
                ignore_keys_for_eval=ignore_keys_for_eval,
                start_time=start_time,
                resume_from_checkpoint=resume_from_checkpoint,
                epochs_trained=epochs_trained,
                steps_trained_in_current_epoch=steps_trained_in_current_epoch,
            )
            if self.control.should_training_stop:
                break

        return self._finalize_training(trial, num_train_samples, start_time)
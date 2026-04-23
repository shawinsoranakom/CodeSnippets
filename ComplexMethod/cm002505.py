def _load_optimizer_and_scheduler(self, checkpoint: str | None) -> None:
        """If optimizer and scheduler states exist, load them."""
        if checkpoint is None:
            return

        if self.is_deepspeed_enabled:
            # deepspeed loads optimizer/lr_scheduler together with the model in deepspeed_init
            if not isinstance(self.lr_scheduler, DeepSpeedSchedulerWrapper):
                with warnings.catch_warnings(record=True) as caught_warnings:
                    check_torch_load_is_safe()
                    self.lr_scheduler.load_state_dict(
                        torch.load(os.path.join(checkpoint, SCHEDULER_NAME), weights_only=True)
                    )
                reissue_pt_warnings(caught_warnings)
            return

        checkpoint_file_exists = (
            glob.glob(os.path.join(checkpoint, OPTIMIZER_NAME) + "_*")
            if is_sagemaker_mp_enabled()
            else (
                os.path.isfile(os.path.join(checkpoint, OPTIMIZER_NAME))
                or os.path.isfile(os.path.join(checkpoint, OPTIMIZER_NAME_BIN))
                or (
                    os.path.isdir(checkpoint)
                    and any(
                        OPTIMIZER_NAME_BIN.split(".")[0] in folder_name
                        for folder_name in os.listdir(checkpoint)
                        if os.path.isdir(os.path.join(checkpoint, folder_name))
                    )
                )
            )
        )
        checkpoint_file_exists = (
            glob.glob(os.path.join(checkpoint, f"rank*-of-{self.args.world_size}-{OPTIMIZER_NAME}"))
            if self.is_fsdp_xla_v1_enabled
            else checkpoint_file_exists
        )
        if checkpoint_file_exists and os.path.isfile(os.path.join(checkpoint, SCHEDULER_NAME)):
            # Load in optimizer and scheduler states
            if is_torch_xla_available():
                # On TPU we have to take some extra precautions to properly load the states on the right device.
                if self.is_fsdp_xla_v1_enabled:
                    check_torch_load_is_safe()
                    optimizer_state = torch.load(
                        os.path.join(
                            checkpoint, f"rank{self.args.process_index}-of-{self.args.world_size}-{OPTIMIZER_NAME}"
                        ),
                        map_location="cpu",
                        weights_only=True,
                    )
                    # We only need `optimizer` when resuming from checkpoint
                    optimizer_state = optimizer_state["optimizer"]
                else:
                    check_torch_load_is_safe()
                    optimizer_state = torch.load(
                        os.path.join(checkpoint, OPTIMIZER_NAME), map_location="cpu", weights_only=True
                    )
                with warnings.catch_warnings(record=True) as caught_warnings:
                    check_torch_load_is_safe()
                    lr_scheduler_state = torch.load(
                        os.path.join(checkpoint, SCHEDULER_NAME), map_location="cpu", weights_only=True
                    )
                reissue_pt_warnings(caught_warnings)

                xm.send_cpu_data_to_device(optimizer_state, self.args.device)
                xm.send_cpu_data_to_device(lr_scheduler_state, self.args.device)

                self.optimizer.load_state_dict(optimizer_state)
                self.lr_scheduler.load_state_dict(lr_scheduler_state)
            else:
                if is_sagemaker_mp_enabled():

                    def opt_load_hook(mod, opt):
                        opt.load_state_dict(smp.load(os.path.join(checkpoint, OPTIMIZER_NAME), partial=True))

                    self.model_wrapped.register_post_step_hook(opt_load_hook)
                else:
                    # We use the CPU when training on one GPU to avoid OOM for GPU RAM when training big models.
                    # In distributed training however, we load directly on each GPU and risk the GPU OOM as it's more
                    # likely to get OOM on CPU (since we load num_gpu times the optimizer state
                    map_location = self.args.device if self.args.world_size > 1 else "cpu"
                    if self.is_fsdp_enabled:
                        load_fsdp_optimizer(
                            self.accelerator.state.fsdp_plugin,
                            self.accelerator,
                            self.optimizer,
                            self.model,
                            checkpoint,
                            **get_fsdp_ckpt_kwargs(),
                        )
                    else:
                        check_torch_load_is_safe()
                        self.optimizer.load_state_dict(
                            torch.load(
                                os.path.join(checkpoint, OPTIMIZER_NAME), map_location=map_location, weights_only=True
                            )
                        )
                with warnings.catch_warnings(record=True) as caught_warnings:
                    check_torch_load_is_safe()
                    self.lr_scheduler.load_state_dict(
                        torch.load(os.path.join(checkpoint, SCHEDULER_NAME), weights_only=True)
                    )
                reissue_pt_warnings(caught_warnings)
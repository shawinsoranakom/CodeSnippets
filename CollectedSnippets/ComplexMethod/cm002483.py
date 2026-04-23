def _prepare_for_training(self, max_steps, train_dataloader, resume_from_checkpoint):
        """Wrap model, create optimizer and scheduler, and run accelerator.prepare. Returns (model, train_dataloader)."""
        delay_optimizer_creation = is_sagemaker_mp_enabled() or self.is_fsdp_xla_enabled or self.is_fsdp_enabled

        # Can't delay optimizer creation when using FSDP2: https://github.com/huggingface/accelerate/blob/3f636d626063ffcf9a337c7d3624d61b7d187d59/src/accelerate/accelerator.py#L1404
        is_fsdp2 = self.is_fsdp_enabled and (getattr(self.accelerator.state.fsdp_plugin, "fsdp_version", 1) == 2)
        if is_fsdp2:
            delay_optimizer_creation = False

        # We need to reset the scheduler, as its parameters may be different on subsequent calls
        if self._created_lr_scheduler:
            self.lr_scheduler = None
            self._created_lr_scheduler = False

        if self.is_deepspeed_enabled:
            self.optimizer, self.lr_scheduler = deepspeed_init(self, num_training_steps=max_steps)

        if not delay_optimizer_creation:
            self.create_optimizer()

        # Pass `self.model_wrapped` so that `_wrap_model` can detect if the model is already
        # wrapped (e.g. in DataParallel) on subsequent `train()` calls and avoid double wrapping.
        model = self._wrap_model(self.model_wrapped)

        # If the model is wrapped, don't use `accelerator.prepare`
        # this is for unhandled cases in accelerate such as FSDP-XLA, SageMaker MP/DP, DataParallel
        use_accelerator_prepare = model is self.model

        # prepare using `accelerator` prepare
        if use_accelerator_prepare:
            if delay_optimizer_creation:
                # TODO: check if we can move this somewhere else
                if self.is_fsdp_enabled and _is_peft_model(self.model):
                    update_fsdp_plugin_peft(self.model, self.accelerator)
                # we only prepare the model as we don't have an optimizer
                model = self.accelerator.prepare(self.model)
                # using the model we prepared to create the optimizer
                self.create_optimizer(model)
                self.optimizer = self.accelerator.prepare(self.optimizer)
            elif self.is_deepspeed_enabled and type(self.lr_scheduler).__name__ == "DummyScheduler":
                model, self.optimizer, self.lr_scheduler = self.accelerator.prepare(
                    self.model, self.optimizer, self.lr_scheduler
                )
            else:
                model, self.optimizer = self.accelerator.prepare(self.model, self.optimizer)
        else:
            self.optimizer = self.accelerator.prepare(self.optimizer)

        # Create scheduler now that the optimizer won't change anymore
        self.create_scheduler(num_training_steps=max_steps)

        # updating self.model_wrapped
        self.model_wrapped = model

        if self.is_fsdp_enabled or self.is_fsdp_xla_enabled:
            # breaking convention for FSDP model
            # TODO: check if this is really needed
            self.model = self.model_wrapped = model

        # backward compatibility
        # TODO: check if we really need this
        if self.is_deepspeed_enabled:
            self.deepspeed = self.model_wrapped

        # Important: at this point:
        # self.model         is the Transformers Model except when we are using FSDP
        # self.model_wrapped is DDP(Transformers Model), Deepspeed(Transformers Model),
        # FSDP(Transformers Model), Dynamo Optimized Module(Transformers Model) etc.

        if self.is_fsdp_enabled:
            # Fix `got mixed torch.Tensor and DTensor` error in model.generate() for FSDP2 with LoRA
            if hasattr(self.model, "generate"):
                dist.fsdp.register_fsdp_forward_method(self.model, "generate")

        # since DataLoader was Accelerate prepared w/o a model arg in the same call, we now have to complete the DL wrapping for ALST/UlyssesSP, after model has been prepared
        pc = getattr(self.accelerator, "parallelism_config", None)
        if pc is not None and pc.sp_backend == "deepspeed" and pc.sp_enabled:
            train_dataloader = self.accelerator.deepspeed_ulysses_dl_adapter(train_dataloader, model)

        # load checkpoint
        if resume_from_checkpoint is not None:
            if self.is_deepspeed_enabled:
                deepspeed_load_checkpoint(
                    self.model_wrapped, resume_from_checkpoint, load_module_strict=not _is_peft_model(self.model)
                )
            elif is_sagemaker_mp_enabled() or self.is_fsdp_enabled:
                self._load_from_checkpoint(resume_from_checkpoint, self.model_wrapped)

            self._load_optimizer_and_scheduler(resume_from_checkpoint)
            self._load_scaler(resume_from_checkpoint)

        # Update the references for the callback_handler
        for attr in ("model", "optimizer", "lr_scheduler"):
            setattr(self.callback_handler, attr, getattr(self, attr))
        self.callback_handler.train_dataloader = train_dataloader

        return model, train_dataloader
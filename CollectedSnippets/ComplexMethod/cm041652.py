def __init__(
        self,
        args: TrainingArguments,
        model: HFModel,
        renderer: Renderer,
        train_dataset: TorchDataset,
        callbacks: list[TrainerCallback] | None = None,
    ) -> None:
        self.args = args
        self.model = model
        self.renderer = renderer
        self.train_dataset = train_dataset

        # info
        self.global_step = 0

        # cached variables
        self.device = DistributedInterface().current_device
        self.dp_size = DistributedInterface().get_world_size(Dim.DP)
        self.cp_size = DistributedInterface().get_world_size(Dim.CP)
        self.model_input_names = self.renderer.processor.model_input_names

        self._create_batch_generator()
        # Calculate num_training_steps: max_steps takes priority if set
        if self.args.max_steps is not None and self.args.max_steps > 0:
            self.num_training_steps = self.args.max_steps
        else:
            self.num_training_steps = self.args.num_train_epochs * len(self.train_batch_generator)

        if self.args.save_epochs is not None:
            steps_per_epoch = len(self.train_batch_generator)
            self.args.save_steps = max(1, int(steps_per_epoch * self.args.save_epochs))

        if self.args.enable_activation_checkpointing:
            self.model.gradient_checkpointing_enable({"use_reentrant": False})

        self._deepspeed_engine = None
        dist_name = self.args.dist_config.name if self.args.dist_config is not None else None

        if dist_name == "deepspeed":
            from ..plugins.trainer_plugins.distributed.hub import DistributedPlugin

            self._deepspeed_engine = DistributedPlugin("deepspeed")(
                self.model,
                self.args.dist_config,
                num_micro_batch=self.train_batch_generator.num_micro_batch,
                micro_batch_size=self.args.micro_batch_size,
            )
            self._init_optimizer()
            self._init_lr_scheduler()
            self.model, self.optimizer, self.lr_scheduler = self._deepspeed_engine.prepare(
                self.model, self.optimizer, self.lr_scheduler
            )
        else:
            # fsdp2 / DDP / no dist
            self._shard_model()
            self._init_optimizer()
            self._init_lr_scheduler()

        self._resume_epoch = 0
        self._checkpoint = TrainingCheckpointCoordinator(self)
        if self.args.resume_from_checkpoint:
            self._checkpoint.resume(self.args.resume_from_checkpoint)

        if self.args.save_ckpt_as_hf:
            logger.warning_rank0(
                "save_ckpt_as_hf is enabled. Intermediate checkpoints will be saved in Hugging Face format. "
                "Note that this will significantly increase memory consumption during saving."
            )

        # Callbacks
        self.callback_handler = CallbackHandler([LoggingCallback()], trainer=self)
        for cb in callbacks or []:
            self.callback_handler.add_callback(cb)

        # Callbacks: TrainerState tracks progress across the full run.
        self.state = TrainerState(
            num_training_steps=self.num_training_steps,
            global_step=self.global_step,
            epoch=self._resume_epoch,
        )

        if self.args.dist_config is not None and self.args.dist_config.get("cp_size", 1) > 1:
            # qwen3.5 is not supported because of the different attention implementation, which will be supported in the future.
            if model.config.model_type == "qwen3_5":
                raise RuntimeError(
                    "Sequence parallel is not supported for qwen3.5 model due to its different attention implementation, which will be supported in the future."
                )
            from ..plugins.model_plugins.parallelization.sequence_parallel import SequenceParallelModelPlugin

            if model.config._attn_implementation != "flash_attention_2":
                logger.warning_rank0(
                    "Sequence parallelism is optimized for flash attention only. Replace the attention implementation to flash_attention_2."
                )
                model.config._attn_implementation = "flash_attention_2"
            SequenceParallelModelPlugin(self.args.dist_config.get("cp_mode", "ulysses"))(model, self.args.dist_config)
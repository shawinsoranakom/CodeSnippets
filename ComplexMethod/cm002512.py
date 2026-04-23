def _hp_search_setup(self, trial: "optuna.Trial | dict[str, Any] | None") -> None:
        """Set up training arguments and accelerator state for a hyperparameter search trial."""
        self._trial = trial

        if self.hp_search_backend is None or trial is None:
            return
        if self.hp_search_backend == HPSearchBackend.OPTUNA:
            params = self.hp_space(trial)
        elif self.hp_search_backend == HPSearchBackend.RAY:
            params = trial
            params.pop("wandb", None)
        elif self.hp_search_backend == HPSearchBackend.WANDB:
            params = trial

        for key, value in params.items():
            if not hasattr(self.args, key):
                logger.warning(
                    f"Trying to set {key} in the hyperparameter search but there is no corresponding field in"
                    " `TrainingArguments`."
                )
                continue
            old_attr = getattr(self.args, key, None)
            # Casting value to the proper type
            if old_attr is not None:
                value = type(old_attr)(value)

            setattr(self.args, key, value)
        if self.hp_search_backend == HPSearchBackend.OPTUNA:
            logger.info(f"Trial: {trial.params}")
        if self.hp_search_backend == HPSearchBackend.WANDB:
            logger.info(f"W&B Sweep parameters: {trial}")
        if self.is_deepspeed_enabled:
            if self.args.deepspeed is None:
                raise ValueError("For sweeps with deepspeed, `args.deepspeed` must be set")

            self.accelerator.free_memory()

            # Rebuild the deepspeed config to reflect the updated training parameters
            from accelerate.utils import DeepSpeedPlugin

            from transformers.integrations.deepspeed import HfTrainerDeepSpeedConfig

            self.args.hf_deepspeed_config = HfTrainerDeepSpeedConfig(self.args.deepspeed)
            self.args.hf_deepspeed_config.trainer_config_process(self.args)
            self.args.deepspeed_plugin = DeepSpeedPlugin(hf_ds_config=self.args.hf_deepspeed_config)

            # From 1.0 on, we need to fully wipe the DS plugin when doing sweeps.
            # Simply calling `_reset_state` is enough and doesn't need a version pin.
            AcceleratorState()._reset_state()

        # `train_batch_size` might change when using HPO https://github.com/huggingface/transformers/pull/18918
        self._train_batch_size = self.args.train_batch_size
        self.create_accelerator_and_postprocess()
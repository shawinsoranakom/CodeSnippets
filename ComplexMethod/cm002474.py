def create_accelerator_and_postprocess(self) -> None:
        """Create the accelerator and perform post-creation setup (FSDP, DeepSpeed, etc.)."""
        # We explicitly don't rely on the `Accelerator` to do gradient accumulation
        grad_acc_kwargs = {}
        if self.args.accelerator_config.gradient_accumulation_kwargs is not None:
            grad_acc_kwargs = self.args.accelerator_config.gradient_accumulation_kwargs

        # check if num_steps is attempted to be passed in gradient_accumulation_kwargs
        if "num_steps" in grad_acc_kwargs:
            if self.args.gradient_accumulation_steps > 1:
                # raise because we do not know which setting is intended.
                raise ValueError(
                    "The `AcceleratorConfig`'s `num_steps` is set but `gradient_accumulation_steps` is greater than 1 in the passed `TrainingArguments`"
                    "If using the passed `AcceleratorConfig` is desired, do not set the `TrainingArguments` `gradient_accumulation_steps`."
                )
            else:
                self.args.gradient_accumulation_steps = grad_acc_kwargs["num_steps"]

        # The Trainer handles GAS itself, so GAS=1 in Accelerate to avoid any double-division
        grad_acc_kwargs["num_steps"] = 1

        # Just making sure that gradient_state have the correct values passed.
        # We don't rely on `accumulate` from accelerate to set sync_gradients in gradient_state.
        # Rather, we do it ourselves by setting self.accelerator.gradient_state._set_sync_gradients.
        gradient_accumulation_plugin = GradientAccumulationPlugin(**grad_acc_kwargs)

        accelerator_config = self.args.accelerator_config.to_dict()

        # Extract dataloader config params from accelerator config
        dataloader_params = ["split_batches", "dispatch_batches", "even_batches", "use_seedable_sampler"]
        dataloader_config = DataLoaderConfiguration(
            **{param: accelerator_config.pop(param) for param in dataloader_params}
        )
        dataloader_config.data_seed = self.args.data_seed

        non_blocking = accelerator_config.pop("non_blocking")

        if non_blocking and not self.args.dataloader_pin_memory:
            logger.warning(
                "`non_blocking` is enabled but `dataloader_pin_memory` is not. For the best performance, it's recommended to enable both."
            )
        dataloader_config.non_blocking = non_blocking
        # this would have been updated above, no need for it anymore
        accelerator_config.pop("gradient_accumulation_kwargs")

        fsdp_plugin = None
        if self.args.fsdp_plugin_args is not None:
            from accelerate.utils import FullyShardedDataParallelPlugin

            fsdp_plugin = FullyShardedDataParallelPlugin(**self.args.fsdp_plugin_args)

        args = self._build_accelerator_args(
            dataloader_config=dataloader_config,
            fsdp_plugin=fsdp_plugin,
            gradient_accumulation_plugin=gradient_accumulation_plugin,
        )

        # create accelerator object
        self.accelerator = Accelerator(**args)
        # some Trainer classes need to use `gather` instead of `gather_for_metrics`, thus we store a flag
        self.gather_function = self.accelerator.gather_for_metrics

        if "use_gather_object" in inspect.signature(self.gather_function).parameters:
            self.gather_function = functools.partial(
                self.gather_function, use_gather_object=self.args.eval_use_gather_object
            )

        # deepspeed and accelerate flags covering both trainer args and accelerate launcher
        self.is_deepspeed_enabled = getattr(self.accelerator.state, "deepspeed_plugin", None) is not None
        self.is_fsdp_enabled = getattr(self.accelerator.state, "fsdp_plugin", None) is not None

        # post accelerator creation setup
        if self.is_fsdp_enabled:
            fsdp_plugin = self.accelerator.state.fsdp_plugin
            for param in ["limit_all_gathers", "activation_checkpointing"]:
                setattr(fsdp_plugin, param, self.args.fsdp_config.get(param, getattr(fsdp_plugin, param)))
            if fsdp_plugin.activation_checkpointing and self.args.gradient_checkpointing:
                raise ValueError(
                    "The activation_checkpointing in FSDP config and the gradient_checkpointing in training arg "
                    "can't be set to True simultaneously. Please use FSDP's activation_checkpointing logic "
                    "when using FSDP."
                )

        if self.is_deepspeed_enabled and getattr(self.args, "hf_deepspeed_config", None) is None:
            propagate_args_to_deepspeed(self.accelerator, self.args)

        # `save_only_model` can't be used with DeepSpeed/FSDP along with `load_best_model_at_end`
        if (
            self.args.save_only_model
            and (self.is_deepspeed_enabled or self.is_fsdp_enabled)
            and self.args.load_best_model_at_end
        ):
            wrapper = "DeepSpeed" if self.is_deepspeed_enabled else "FSDP"
            raise ValueError(f"{wrapper} can't be used with `save_only_model` along with `load_best_model_at_end`.")

        # `auto_find_batch_size` isn't supported yet with DeepSpeed Zero-3
        if (
            self.is_deepspeed_enabled
            and self.accelerator.state.deepspeed_plugin.zero_stage == 3
            and self.args.auto_find_batch_size
        ):
            raise ValueError(
                "`auto_find_batch_size` isn't supported yet with DeepSpeed Zero-3. Please consider using Zero-2, Zero-1, or FSDP"
            )
        if (
            self.args.save_only_model
            and self.is_fsdp_enabled
            and "SHARDED_STATE_DICT" in str(self.accelerator.state.fsdp_plugin.state_dict_type)
        ):
            raise ValueError("save_only_model option is not compatible with FSDP state dict type 'SHARDED_STATE_DICT'")
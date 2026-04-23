def _load_best_model(self) -> None:
        """Load the best model found during training based on the tracked metric."""
        logger.info(f"Loading best model from {self.state.best_model_checkpoint} (score: {self.state.best_metric}).")
        best_model_path = os.path.join(self.state.best_model_checkpoint, WEIGHTS_NAME)
        best_safe_model_path = os.path.join(self.state.best_model_checkpoint, SAFE_WEIGHTS_NAME)
        best_adapter_model_path = os.path.join(self.state.best_model_checkpoint, ADAPTER_WEIGHTS_NAME)
        best_safe_adapter_model_path = os.path.join(self.state.best_model_checkpoint, ADAPTER_SAFE_WEIGHTS_NAME)

        model = self.model_wrapped if is_sagemaker_mp_enabled() else self.model
        if self.is_deepspeed_enabled:
            deepspeed_load_checkpoint(
                self.model_wrapped,
                self.state.best_model_checkpoint,
                load_module_strict=not _is_peft_model(self.model),
            )
        elif self.is_fsdp_enabled:
            load_result = load_fsdp_model(
                self.accelerator.state.fsdp_plugin,
                self.accelerator,
                model,
                self.state.best_model_checkpoint,
                **get_fsdp_ckpt_kwargs(),
            )
        elif (
            os.path.exists(best_model_path)
            or os.path.exists(best_safe_model_path)
            or os.path.exists(best_adapter_model_path)
            or os.path.exists(best_safe_adapter_model_path)
        ):
            has_been_loaded = True
            if is_sagemaker_mp_enabled():
                smp.resume_from_checkpoint(
                    path=self.state.best_model_checkpoint,
                    tag=WEIGHTS_NAME,
                    partial=False,
                    load_optimizer=False,
                )
            else:
                if _is_peft_model(model):
                    # If training a model using PEFT, assume that adapter have been saved properly.
                    if hasattr(model, "active_adapters") and hasattr(model, "load_adapter"):
                        active_adapter = model.active_adapters[0]
                        if len(model.active_adapters) > 1:
                            logger.warning("Detected multiple active adapters, will only consider the first one")

                        if os.path.exists(best_adapter_model_path) or os.path.exists(best_safe_adapter_model_path):
                            try:
                                model.load_adapter(self.state.best_model_checkpoint, active_adapter)
                            except RuntimeError as exc:
                                if model.peft_config[active_adapter].is_prompt_learning:
                                    # for context: https://github.com/huggingface/peft/issues/2256
                                    msg = (
                                        "When using prompt learning PEFT methods such as "
                                        f"{model.peft_config[active_adapter].peft_type.value}, setting "
                                        "load_best_model_at_end=True can lead to errors, it is recommended "
                                        "to set this to False and to load the model manually from the checkpoint "
                                        "directory using PeftModel.from_pretrained(base_model, <path>) after training "
                                        "has finished."
                                    )
                                    raise RuntimeError(msg) from exc
                                else:
                                    raise
                            # Load_adapter has no return value present, modify it when appropriate.
                            from torch.nn.modules.module import _IncompatibleKeys

                            load_result = _IncompatibleKeys([], [])
                        else:
                            logger.warning(
                                "The intermediate checkpoints of PEFT may not be saved correctly, "
                                f"consider using a custom callback to save {ADAPTER_WEIGHTS_NAME} in corresponding saving folders. "
                                "Check some examples here: https://github.com/huggingface/peft/issues/96"
                            )
                            has_been_loaded = False
                    else:
                        logger.warning(
                            f"Could not load adapter model, make sure to have PEFT >= {MIN_PEFT_VERSION} installed"
                        )
                        has_been_loaded = False
                else:
                    # We load the model state dict on the CPU to avoid an OOM error.
                    if os.path.isfile(best_safe_model_path):
                        state_dict = safetensors.torch.load_file(best_safe_model_path, device="cpu")
                    else:
                        check_torch_load_is_safe()
                        state_dict = torch.load(best_model_path, map_location="cpu", weights_only=True)

                    # If the model is on the GPU, it still works!
                    # workaround for FSDP bug https://github.com/pytorch/pytorch/issues/82963
                    # which takes *args instead of **kwargs
                    load_result = model.load_state_dict(state_dict, False)
                if not is_sagemaker_mp_enabled() and has_been_loaded:
                    self._issue_warnings_after_load(load_result)
        elif os.path.exists(os.path.join(self.state.best_model_checkpoint, SAFE_WEIGHTS_INDEX_NAME)) or os.path.exists(
            os.path.join(self.state.best_model_checkpoint, WEIGHTS_INDEX_NAME)
        ):
            load_result = load_sharded_checkpoint(
                model, self.state.best_model_checkpoint, strict=is_sagemaker_mp_enabled()
            )
            if not is_sagemaker_mp_enabled():
                self._issue_warnings_after_load(load_result)
        else:
            logger.warning(
                f"Could not locate the best model at {best_model_path}, if you are running a distributed training "
                "on multiple nodes, you should activate `--save_on_each_node`."
            )
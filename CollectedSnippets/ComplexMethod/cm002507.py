def save_model(self, output_dir: str | None = None, _internal_call: bool = False) -> None:
        """
        Will save the model, so you can reload it using `from_pretrained()`.

        Will only save from the main process.
        """

        if output_dir is None:
            output_dir = self.args.output_dir

        if is_torch_xla_available():
            save_tpu_checkpoint(
                self.model, self.args, self.accelerator, self.processing_class, self.is_fsdp_xla_v1_enabled, output_dir
            )
        elif is_sagemaker_mp_enabled():
            # Calling the state_dict needs to be done on the wrapped model and on all processes.
            os.makedirs(output_dir, exist_ok=True)
            state_dict = self.model_wrapped.state_dict()
            if self.args.should_save:
                self._save(output_dir, state_dict=state_dict)
            Path(os.path.join(output_dir, "user_content.pt")).touch()
        elif self.is_fsdp_enabled:
            if "FULL_STATE_DICT" in str(self.accelerator.state.fsdp_plugin.state_dict_type):
                state_dict = self.accelerator.get_state_dict(self.model)
                if self.args.should_save:
                    self._save(output_dir, state_dict=state_dict)
        elif self.is_deepspeed_enabled:
            try:
                accept_exclude_frozen_parameters = "exclude_frozen_parameters" in set(
                    inspect.signature(self.model_wrapped.save_checkpoint).parameters.keys()
                )
                zero3_sharding = self.deepspeed.config.get("zero_optimization", {}).get("stage", None) == 3
                if accept_exclude_frozen_parameters and _is_peft_model(self.model) and zero3_sharding:
                    # When using PEFT with DeepSpeed ZeRO Stage 3,
                    # we do not need to load the frozen parameters
                    state_dict = self.deepspeed._zero3_consolidated_16bit_state_dict(exclude_frozen_parameters=True)
                else:
                    state_dict = self.accelerator.get_state_dict(self.deepspeed)
                if self.args.should_save:
                    self._save(output_dir, state_dict=state_dict)
            except ValueError:
                logger.warning(
                    " stage3_gather_16bit_weights_on_model_save=false. Saving the full checkpoint instead, use"
                    " zero_to_fp32.py to recover weights"
                )
                if self.args.should_save:
                    self._save(output_dir, state_dict={})
                # remove the dummy state_dict
                remove_dummy_checkpoint(self.args.should_save, output_dir, [WEIGHTS_NAME, SAFE_WEIGHTS_NAME])
                self.model_wrapped.save_checkpoint(output_dir)

        elif self.args.should_save:
            self._save(output_dir)

        # Push to the Hub when `save_model` is called by the user.
        if self.args.push_to_hub and not _internal_call:
            self.push_to_hub(commit_message="Model save", revision=self.args.hub_revision)
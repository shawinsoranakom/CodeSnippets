def setup(self, args, state, model, **kwargs):
        """
        Setup the optional Trackio integration.

        To customize the setup you can also set `project`, `trackio_space_id`, `trackio_bucket_id`,
        `trackio_static_space_id`, and `hub_private_repo` in [`TrainingArguments`].
        """
        if state.is_world_process_zero:
            combined_dict = {**args.to_dict()}
            if hasattr(model, "config") and model.config is not None:
                model_config = model.config if isinstance(model.config, dict) else model.config.to_dict()
                combined_dict = {**model_config, **combined_dict}
            if hasattr(model, "peft_config") and model.peft_config is not None:
                peft_config = model.peft_config
                combined_dict = {"peft_config": peft_config, **combined_dict}

            self._trackio.init(
                project=args.project,
                name=args.run_name,
                space_id=args.trackio_space_id,
                resume="allow",
                private=args.hub_private_repo,
                bucket_id=args.trackio_bucket_id,
            )
            # The Trackio space_id may have been set by an environment variable, or set explicitly in the training arguments
            # but without the full space_id. This ensures that self._space_id is set to the full space_id.
            self._space_id = self._trackio.context_vars.current_space_id.get()
            # Add config parameters (run may have been created manually)
            self._trackio.config.update(combined_dict, allow_val_change=True)

            # Add number of model parameters to trackio config
            try:
                self._trackio.config["model/num_parameters"] = model.num_parameters()
            except AttributeError:
                logger.info("Could not log the number of model parameters in Trackio due to an AttributeError.")
        self._initialized = True
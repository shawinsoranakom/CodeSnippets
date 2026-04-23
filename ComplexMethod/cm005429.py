def setup(self, args, state, model, **kwargs):
        """
        Setup the optional Weights & Biases (*wandb*) integration.

        One can subclass and override this method to customize the setup if needed. Find more information
        [here](https://docs.wandb.ai/guides/integrations/huggingface). You can also override the following environment
        variables:

        Environment:
        - **WANDB_LOG_MODEL** (`str`, *optional*, defaults to `"false"`):
            Whether to log model and checkpoints during training. Can be `"end"`, `"checkpoint"` or `"false"`. If set
            to `"end"`, the model will be uploaded at the end of training. If set to `"checkpoint"`, the checkpoint
            will be uploaded every `args.save_steps` . If set to `"false"`, the model will not be uploaded. Use along
            with [`~transformers.TrainingArguments.load_best_model_at_end`] to upload best model.
        - **WANDB_WATCH** (`str`, *optional* defaults to `"false"`):
            Can be `"gradients"`, `"all"`, `"parameters"`, or `"false"`. Set to `"all"` to log gradients and
            parameters.
        - **WANDB_PROJECT** (`str`, *optional*, defaults to `"huggingface"`):
            Set this to a custom string to store results in a different project.
        """
        if self._wandb is None:
            return
        self._initialized = True

        # prepare to handle potential configuration issues during setup
        from wandb.sdk.lib.config_util import ConfigError as WandbConfigError

        if state.is_world_process_zero:
            combined_dict = {**args.to_dict()}

            if hasattr(model, "config") and model.config is not None:
                model_config = model.config if isinstance(model.config, dict) else model.config.to_dict()
                combined_dict = {**model_config, **combined_dict}
            if hasattr(model, "peft_config") and model.peft_config is not None:
                peft_config = model.peft_config
                combined_dict = {"peft_config": peft_config, **combined_dict}
            trial_name = state.trial_name
            init_args = {}
            if trial_name is not None:
                init_args["name"] = trial_name
                init_args["group"] = args.run_name or args.output_dir
            elif args.run_name is not None:
                init_args["name"] = args.run_name
                if args.run_name == args.output_dir:
                    self._wandb.termwarn(
                        "The `run_name` is currently set to the same value as `TrainingArguments.output_dir`. If this was "
                        "not intended, please specify a different run name by setting the `TrainingArguments.run_name` parameter.",
                        repeat=False,
                    )

            if self._wandb.run is None:
                self._wandb.init(
                    project=os.getenv("WANDB_PROJECT", "huggingface"),
                    **init_args,
                )
            # add config parameters (run may have been created manually)
            self._wandb.config.update(combined_dict or {}, allow_val_change=True)

            # define default x-axis (for latest wandb versions)
            if getattr(self._wandb, "define_metric", None):
                self._wandb.define_metric("train/global_step")
                self._wandb.define_metric("*", step_metric="train/global_step", step_sync=True)

            # keep track of model topology and gradients, unsupported on TPU
            _watch_model = os.getenv("WANDB_WATCH", "false")
            if not is_torch_xla_available() and _watch_model in ("all", "parameters", "gradients"):
                self._wandb.watch(model, log=_watch_model, log_freq=max(100, state.logging_steps))
            self._wandb.run._label(code="transformers_trainer")

            # add number of model parameters to wandb config
            try:
                self._wandb.config["model/num_parameters"] = model.num_parameters()
            except AttributeError:
                logger.info(
                    "Could not log the number of model parameters in Weights & Biases due to an AttributeError."
                )
            except WandbConfigError:
                logger.warning(
                    "A ConfigError was raised whilst setting the number of model parameters in Weights & Biases config."
                )

            # log the initial model architecture to an artifact
            if self._log_model.is_enabled:
                with tempfile.TemporaryDirectory() as temp_dir:
                    model_name = (
                        f"model-{self._wandb.run.id}"
                        if (args.run_name is None or args.run_name == args.output_dir)
                        else f"model-{self._wandb.run.name}"
                    )
                    model_artifact = self._wandb.Artifact(
                        name=model_name,
                        type="model",
                        metadata={
                            "model_config": model.config.to_dict() if hasattr(model, "config") else None,
                            "num_parameters": self._wandb.config.get("model/num_parameters"),
                            "initial_model": True,
                        },
                    )
                    # add the architecture to a separate text file
                    save_model_architecture_to_file(model, temp_dir)

                    for f in Path(temp_dir).glob("*"):
                        if f.is_file():
                            with model_artifact.new_file(f.name, mode="wb") as fa:
                                fa.write(f.read_bytes())
                    self._wandb.run.log_artifact(model_artifact, aliases=["base_model"])

                    badge_markdown = (
                        f'[<img src="https://raw.githubusercontent.com/wandb/assets/main/wandb-github-badge'
                        f'-28.svg" alt="Visualize in Weights & Biases" width="20'
                        f'0" height="32"/>]({self._wandb.run.url})'
                    )

                    modelcard.AUTOGENERATED_TRAINER_COMMENT += f"\n{badge_markdown}"
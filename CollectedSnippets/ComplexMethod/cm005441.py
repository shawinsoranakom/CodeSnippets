def setup(self, args, state, model, **kwargs):
        """
        Setup the optional SwanLab (*swanlab*) integration.

        One can subclass and override this method to customize the setup if needed. Find more information
        [here](https://docs.swanlab.cn/guide_cloud/integration/integration-huggingface-transformers.html).

        You can also override the following environment variables. Find more information about environment
        variables [here](https://docs.swanlab.cn/en/api/environment-variable.html#environment-variables)

        Environment:
        - **SWANLAB_API_KEY** (`str`, *optional*, defaults to `None`):
            Cloud API Key. During login, this environment variable is checked first. If it doesn't exist, the system
            checks if the user is already logged in. If not, the login process is initiated.

                - If a string is passed to the login interface, this environment variable is ignored.
                - If the user is already logged in, this environment variable takes precedence over locally stored
                login information.

        - **SWANLAB_PROJECT** (`str`, *optional*, defaults to `None`):
            Set this to a custom string to store results in a different project. If not specified, the name of the current
            running directory is used.

        - **SWANLAB_LOG_DIR** (`str`, *optional*, defaults to `swanlog`):
            This environment variable specifies the storage path for log files when running in local mode.
            By default, logs are saved in a folder named swanlog under the working directory.

        - **SWANLAB_MODE** (`Literal["local", "cloud", "disabled"]`, *optional*, defaults to `cloud`):
            SwanLab's parsing mode, which involves callbacks registered by the operator. Currently, there are three modes:
            local, cloud, and disabled. Note: Case-sensitive. Find more information
            [here](https://docs.swanlab.cn/en/api/py-init.html#swanlab-init)

        - **SWANLAB_LOG_MODEL** (`str`, *optional*, defaults to `None`):
            SwanLab does not currently support the save mode functionality.This feature will be available in a future
            release

        - **SWANLAB_WEB_HOST** (`str`, *optional*, defaults to `None`):
            Web address for the SwanLab cloud environment for private version (its free)

        - **SWANLAB_API_HOST** (`str`, *optional*, defaults to `None`):
            API address for the SwanLab cloud environment for private version (its free)

        - **SWANLAB_RUN_ID** (`str`, *optional*, defaults to `None`):
            Experiment ID to resume a previous run. Use with `SWANLAB_RESUME` to continue an existing experiment.

        - **SWANLAB_RESUME** (`str`, *optional*, defaults to `None`):
            Resume mode (`"must"`, `"allow"`, `"never"`). Defaults to `"allow"` when `resume_from_checkpoint` is used.

        """
        self._initialized = True

        if state.is_world_process_zero:
            logger.info('Automatic SwanLab logging enabled, to disable set os.environ["SWANLAB_MODE"] = "disabled"')
            combined_dict = {**args.to_dict()}

            if hasattr(model, "config") and model.config is not None:
                model_config = model.config if isinstance(model.config, dict) else model.config.to_dict()
                combined_dict = {**model_config, **combined_dict}
            if hasattr(model, "peft_config") and model.peft_config is not None:
                peft_config = model.peft_config
                combined_dict = {"peft_config": peft_config, **combined_dict}
            trial_name = state.trial_name
            init_args = {}
            if trial_name is not None and args.run_name is not None:
                init_args["experiment_name"] = f"{args.run_name}-{trial_name}"
            elif args.run_name is not None:
                init_args["experiment_name"] = args.run_name
            elif trial_name is not None:
                init_args["experiment_name"] = trial_name
            init_args["project"] = os.getenv("SWANLAB_PROJECT", None)

            run_id = os.getenv("SWANLAB_RUN_ID", None)
            if run_id is not None:
                init_args["id"] = run_id

            resume = os.getenv("SWANLAB_RESUME", None)
            if resume is not None:
                init_args["resume"] = resume
            elif args.resume_from_checkpoint:
                init_args["resume"] = "allow"

            if self._swanlab.get_run() is None:
                self._swanlab.init(
                    **init_args,
                )
            # show transformers logo!
            self._swanlab.config["FRAMEWORK"] = "🤗transformers"
            # add config parameters (run may have been created manually)
            self._swanlab.config.update(combined_dict)

            # add number of model parameters to swanlab config
            try:
                self._swanlab.config.update({"model_num_parameters": model.num_parameters()})
                # get peft model parameters
                if type(model).__name__ == "PeftModel" or type(model).__name__ == "PeftMixedModel":
                    trainable_params, all_param = model.get_nb_trainable_parameters()
                    self._swanlab.config.update({"peft_model_trainable_params": trainable_params})
                    self._swanlab.config.update({"peft_model_all_param": all_param})
            except AttributeError:
                logger.info("Could not log the number of model parameters in SwanLab due to an AttributeError.")

            # log the initial model architecture to an artifact
            if self._log_model is not None:
                logger.warning(
                    "SwanLab does not currently support the save mode functionality. "
                    "This feature will be available in a future release."
                )
                badge_markdown = (
                    f'[<img src="https://raw.githubusercontent.com/SwanHubX/assets/main/badge1.svg"'
                    f' alt="Visualize in SwanLab" height="28'
                    f'0" height="32"/>]({self._swanlab.get_run().public.cloud.experiment_url})'
                )

                modelcard.AUTOGENERATED_TRAINER_COMMENT += f"\n{badge_markdown}"
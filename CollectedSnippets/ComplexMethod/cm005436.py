def setup(self, args, state, model):
        """
        Setup the optional Comet integration.

        Environment:
        - **COMET_MODE** (`str`, *optional*, default to `get_or_create`):
            Control whether to create and log to a new Comet experiment or append to an existing experiment.
            It accepts the following values:
                * `get_or_create`: Decides automatically depending if
                  `COMET_EXPERIMENT_KEY` is set and whether an Experiment
                  with that key already exists or not.
                * `create`: Always create a new Comet Experiment.
                * `get`: Always try to append to an Existing Comet Experiment.
                  Requires `COMET_EXPERIMENT_KEY` to be set.
        - **COMET_START_ONLINE** (`bool`, *optional*):
            Whether to create an online or offline Experiment.
        - **COMET_PROJECT_NAME** (`str`, *optional*):
            Comet project name for experiments.
        - **COMET_LOG_ASSETS** (`str`, *optional*, defaults to `TRUE`):
            Whether or not to log training assets (checkpoints, etc), to Comet. Can be `TRUE`, or
            `FALSE`.

        For a number of configurable items in the environment, see
        [here](https://www.comet.com/docs/v2/guides/experiment-management/configure-sdk/#explore-comet-configuration-options).
        """
        self._initialized = True
        log_assets = os.getenv("COMET_LOG_ASSETS", "FALSE").upper()
        if log_assets in {"TRUE", "1"}:
            self._log_assets = True
        if state.is_world_process_zero:
            comet_old_mode = os.getenv("COMET_MODE")

            mode = None
            online = None

            if comet_old_mode is not None:
                comet_old_mode = comet_old_mode.lower()
                if comet_old_mode in ("get", "get_or_create", "create"):
                    mode = comet_old_mode
                elif comet_old_mode:
                    logger.warning("Invalid COMET_MODE env value %r, Comet logging is disabled", comet_old_mode)
                    return

            # For HPO, we always create a new experiment for each trial
            if state.is_hyper_param_search:
                if mode is not None:
                    logger.warning(
                        "Hyperparameter Search is enabled, forcing the creation of new experiments, COMET_MODE value %r  is ignored",
                        comet_old_mode,
                    )
                mode = "create"

            import comet_ml

            experiment_config = comet_ml.ExperimentConfig(name=args.run_name)

            self._experiment = comet_ml.start(online=online, mode=mode, experiment_config=experiment_config)
            self._experiment.__internal_api__set_model_graph__(model, framework="transformers")

            params = {"args": args.to_dict()}

            if hasattr(model, "config") and model.config is not None:
                model_config = model.config.to_dict()
                params["config"] = model_config
            if hasattr(model, "peft_config") and model.peft_config is not None:
                peft_config = model.peft_config
                params["peft_config"] = peft_config

            self._experiment.__internal_api__log_parameters__(
                params, framework="transformers", source="manual", flatten_nested=True
            )

            if state.is_hyper_param_search:
                optimization_id = getattr(state, "trial_name", None)
                optimization_params = getattr(state, "trial_params", None)

                self._experiment.log_optimization(optimization_id=optimization_id, parameters=optimization_params)
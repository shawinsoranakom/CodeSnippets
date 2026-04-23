def setup(self, args, state, model, processing_class, **kwargs):
        if self._clearml is None:
            return
        if self._initialized:
            return
        ClearMLCallback._train_run_counter += 1
        ClearMLCallback._model_connect_counter += 1
        ClearMLCallback.log_suffix = (
            "" if ClearMLCallback._train_run_counter == 1 else "_" + str(ClearMLCallback._train_run_counter)
        )
        if state.is_world_process_zero:
            logger.info("Automatic ClearML logging enabled.")
            if self._clearml_task is None:
                if ClearMLCallback._should_close_on_train_end is None:
                    if not self._clearml.Task.running_locally() or self._clearml.Task.current_task():
                        ClearMLCallback._should_close_on_train_end = False
                    else:
                        ClearMLCallback._should_close_on_train_end = True

                # This might happen when running inside of a pipeline, where the task is already initialized
                # from outside of Hugging Face
                if self._clearml.Task.running_locally() and self._clearml.Task.current_task():
                    self._clearml_task = self._clearml.Task.current_task()
                    self._log_model = os.getenv(
                        "CLEARML_LOG_MODEL",
                        "FALSE" if not ClearMLCallback._task_created_in_callback else "TRUE",
                    ).upper() in ENV_VARS_TRUE_VALUES.union({"TRUE"})
                    logger.info("External ClearML Task has been connected.")
                else:
                    self._clearml_task = self._clearml.Task.init(
                        project_name=os.getenv("CLEARML_PROJECT", "HuggingFace Transformers"),
                        task_name=os.getenv("CLEARML_TASK", "Trainer"),
                        auto_connect_frameworks={"tensorboard": False, "pytorch": False},
                        output_uri=True,
                    )
                    self._log_model = os.getenv("CLEARML_LOG_MODEL", "TRUE").upper() in ENV_VARS_TRUE_VALUES.union(
                        {"TRUE"}
                    )
                    ClearMLCallback._task_created_in_callback = True
                    logger.info("ClearML Task has been initialized.")
                self._initialized = True

            suffixed_hparams_section = ClearMLCallback._hparams_section + ClearMLCallback.log_suffix
            ignore_hparams_config_section = suffixed_hparams_section + "/" + ClearMLCallback._ignore_hparams_overrides
            if self._clearml.Task.running_locally():
                self._copy_training_args_as_hparams(args, suffixed_hparams_section)
                self._clearml_task.set_parameter(
                    name=ignore_hparams_config_section,
                    value=True,
                    value_type=bool,
                    description=(
                        "If True, ignore Transformers hyperparameters overrides done in the UI/backend "
                        + "when running remotely. Otherwise, the overrides will be applied when running remotely"
                    ),
                )
            elif not self._clearml_task.get_parameter(ignore_hparams_config_section, default=True, cast=True):
                self._clearml_task.connect(args, suffixed_hparams_section)
            else:
                self._copy_training_args_as_hparams(
                    args, ClearMLCallback._hparams_section + ClearMLCallback.log_suffix
                )

            if getattr(model, "config", None) is not None:
                ignore_model_config_section = (
                    suffixed_hparams_section + "/" + ClearMLCallback._ignoge_model_config_overrides
                )
                configuration_object_description = ClearMLCallback._model_config_description.format(
                    ClearMLCallback._model_connect_counter
                )
                if ClearMLCallback._model_connect_counter != ClearMLCallback._train_run_counter:
                    configuration_object_description += " " + ClearMLCallback._model_config_description_note
                if self._clearml.Task.running_locally():
                    self._clearml_task.set_parameter(
                        name=ignore_model_config_section,
                        value=True,
                        value_type=bool,
                        description=(
                            "If True, ignore Transformers model configuration overrides done in the UI/backend "
                            + "when running remotely. Otherwise, the overrides will be applied when running remotely"
                        ),
                    )
                    self._clearml_task.set_configuration_object(
                        name=ClearMLCallback._model_config_section + ClearMLCallback.log_suffix,
                        config_dict=model.config.to_dict(),
                        description=configuration_object_description,
                    )
                elif not self._clearml_task.get_parameter(ignore_model_config_section, default=True, cast=True):
                    model.config = model.config.from_dict(
                        self._clearml_task.get_configuration_object_as_dict(
                            ClearMLCallback._model_config_section + ClearMLCallback.log_suffix
                        )
                    )
                else:
                    self._clearml_task.set_configuration_object(
                        name=ClearMLCallback._model_config_section + ClearMLCallback.log_suffix,
                        config_dict=model.config.to_dict(),
                        description=configuration_object_description,
                    )
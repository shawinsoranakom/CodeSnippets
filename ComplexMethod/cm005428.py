def on_train_begin(self, args, state, control, **kwargs):
        if not state.is_world_process_zero:
            return

        if state.is_hyper_param_search:
            trial_name = state.trial_name
            if trial_name is not None:
                # overwrite logging dir for trials
                self.logging_dir = os.path.join(args.output_dir, default_logdir(), trial_name)

        if self.logging_dir is None:
            self.logging_dir = os.path.join(args.output_dir, default_logdir())

        if self.tb_writer is None:
            self._init_summary_writer(args)

        if self.tb_writer is not None:
            self.tb_writer.add_text("args", args.to_json_string())
            if "model" in kwargs:
                model = kwargs["model"]
                if hasattr(model, "config") and model.config is not None:
                    model_config_json = model.config.to_json_string()
                    self.tb_writer.add_text("model_config", model_config_json)
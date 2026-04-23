def _initialize(self, data: dict["Component", Any], do_train: bool, from_preview: bool) -> str:
        r"""Validate the configuration."""
        get = lambda elem_id: data[self.manager.get_elem_by_id(elem_id)]
        lang, model_name, model_path = get("top.lang"), get("top.model_name"), get("top.model_path")
        dataset = get("train.dataset") if do_train else get("eval.dataset")

        if self.running:
            return ALERTS["err_conflict"][lang]

        if not model_name:
            return ALERTS["err_no_model"][lang]

        if not model_path:
            return ALERTS["err_no_path"][lang]

        if not dataset:
            return ALERTS["err_no_dataset"][lang]

        if not from_preview and self.demo_mode:
            return ALERTS["err_demo"][lang]

        if do_train:
            if not get("train.output_dir"):
                return ALERTS["err_no_output_dir"][lang]

            try:
                json.loads(get("train.extra_args"))
            except json.JSONDecodeError:
                return ALERTS["err_json_schema"][lang]

            stage = TRAINING_STAGES[get("train.training_stage")]
            if stage == "ppo" and not get("train.reward_model"):
                return ALERTS["err_no_reward_model"][lang]
        else:
            if not get("eval.output_dir"):
                return ALERTS["err_no_output_dir"][lang]

        if not from_preview and not is_accelerator_available():
            gr.Warning(ALERTS["warn_no_cuda"][lang])

        return ""
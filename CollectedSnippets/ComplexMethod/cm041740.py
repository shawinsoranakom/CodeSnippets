def resume(self):
        r"""Get the initial value of gradio components and restores training status if necessary."""
        user_config = load_config() if not self.demo_mode else {}  # do not use config in demo mode
        lang = user_config.get("lang") or "en"
        init_dict = {"top.lang": {"value": lang}, "infer.chat_box": {"visible": self.chatter.loaded}}

        if not self.pure_chat:
            current_time = get_time()
            hub_name = user_config.get("hub_name") or "huggingface"
            init_dict["top.hub_name"] = {"value": hub_name}
            init_dict["train.current_time"] = {"value": current_time}
            init_dict["train.output_dir"] = {"value": f"train_{current_time}"}
            init_dict["train.config_path"] = {"value": f"{current_time}.yaml"}
            init_dict["eval.output_dir"] = {"value": f"eval_{current_time}"}
            init_dict["infer.mm_box"] = {"visible": False}

            if user_config.get("last_model", None):
                init_dict["top.model_name"] = {"value": user_config["last_model"]}

        yield self._update_component(init_dict)

        if self.runner.running and not self.demo_mode and not self.pure_chat:
            yield {elem: elem.__class__(value=value) for elem, value in self.runner.running_data.items()}
            if self.runner.do_train:
                yield self._update_component({"train.resume_btn": {"value": True}})
            else:
                yield self._update_component({"eval.resume_btn": {"value": True}})
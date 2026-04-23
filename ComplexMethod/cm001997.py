def test_retain_grad_hidden_states_attentions(self):
        """Overwritten to account for the vision suffix before, e.g. `vision_hidden_states`"""
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        for k in config.sub_configs:
            if getattr(config, k) is not None:
                getattr(config, k).output_hidden_states = True

        config.output_hidden_states = True
        config.output_attentions = self.has_attentions

        for k in config.sub_configs:
            if (
                self._is_composite and k == "vision_config"
            ):  # skip because it's not needed and causes errors e.g with Timm
                continue
            if getattr(config, k) is not None:
                getattr(config, k).output_attentions = self.has_attentions

        # force eager attention to support output attentions
        if self.has_attentions:
            config._attn_implementation = "eager"

        # no need to test all models as different heads yield the same functionality
        model_class = self.all_model_classes[0]
        model = model_class._from_config(config, attn_implementation="eager")
        model.to(torch_device)

        inputs = self._prepare_for_class(inputs_dict, model_class)

        outputs = model(**inputs)

        output = outputs[0]

        hidden_states = outputs.vision_hidden_states[0]
        hidden_states.retain_grad()

        if self.has_attentions:
            attentions = outputs.vision_attentions[0]
            attentions.retain_grad()

        output.flatten()[0].backward(retain_graph=True)

        self.assertIsNotNone(hidden_states.grad)

        if self.has_attentions:
            self.assertIsNotNone(attentions.grad)
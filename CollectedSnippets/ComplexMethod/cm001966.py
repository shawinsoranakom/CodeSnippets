def test_retain_grad_hidden_states_attentions(self):
        """
        TimesFM 2.5 specific test for retain_grad since the model returns mean_predictions
        as the first tensor, not last_hidden_state like standard models.
        """
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.output_hidden_states = True
        config.output_attentions = self.has_attentions

        # force eager attention to support output attentions
        if self.has_attentions:
            config._attn_implementation = "eager"

        # no need to test all models as different heads yield the same functionality
        model_class = self.all_model_classes[0]
        model = model_class._from_config(config, attn_implementation="eager")
        model.to(torch_device)

        inputs = self._prepare_for_class(inputs_dict, model_class)

        outputs = model(**inputs)

        # TimesFM 2.5 returns mean_predictions as first output, not last_hidden_state
        output_tensor = outputs.mean_predictions

        # Encoder-/Decoder-only models
        if outputs.hidden_states is not None:
            hidden_states = outputs.hidden_states[0]
            hidden_states.retain_grad()

        if self.has_attentions and outputs.attentions is not None:
            attentions = outputs.attentions[0]
            attentions.retain_grad()

        output_tensor.flatten()[0].backward(retain_graph=True)

        if outputs.hidden_states is not None:
            self.assertIsNotNone(hidden_states.grad)

        if self.has_attentions and outputs.attentions is not None:
            self.assertIsNotNone(attentions.grad)
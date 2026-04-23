def test_flex_attention_with_grads(self):
        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            inputs_dict = self._prepare_for_class(inputs_dict, model_class)
            model = model_class(config).to(device=torch_device)

            # If not all sub-models support flex, skip the test
            if not all(
                submodel._supports_flex_attn for submodel in model.modules() if isinstance(submodel, PreTrainedModel)
            ):
                self.skipTest(reason="At least some parts of this model do not support flex attention")

            # Set default attention to flex and update config values
            config = self._prepare_config_headdim(config, 16)  # specific to triton

            if model_class._can_set_attn_implementation():
                model = model_class(config).to(device=torch_device)
                model.set_attn_implementation("flex_attention")
                self.assertTrue(model.config._attn_implementation == "flex_attention")
            else:
                config._attn_implementation = "flex_attention"
                model = model_class(config).to(device=torch_device)

            # Elaborate workaround for encoder-decoder models as some do not specify their main input
            dummy_inputs = {model.main_input_name: inputs_dict[model.main_input_name].to(torch_device)}
            for key in getattr(self, "additional_model_inputs", []):
                # Some models don't have all `additional_model_inputs`, especially when we
                # craft cases to test model in different settings
                if key in inputs_dict:
                    dummy_inputs[key] = inputs_dict[key].to(torch_device)

            if config.is_encoder_decoder:
                dummy_inputs["decoder_input_ids"] = inputs_dict["decoder_input_ids"].to(torch_device)
                dummy_inputs["decoder_attention_mask"] = inputs_dict["decoder_attention_mask"].to(torch_device)

            # If this does not raise an error, the test passes (see https://github.com/huggingface/transformers/pull/35605)
            _ = model(**dummy_inputs)
def test_attn_implementation_composite_models(self):
        """
        Tests if composite models can receive a dict object as attn_implementation, where each key should be
        one of the sub-configs from the model's config.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        for model_class in self.all_model_classes:
            if not self._is_composite:
                self.skipTest("Model is not a composite model.")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

            # set eager as it will be the one supported in all models
            # we just need to test if passing 'attn_implementation' as a dict fails or not
            attn_implementation_per_subconfig = {"": "eager"}
            for key in config.sub_configs:
                if getattr(config, key) is not None:
                    attn_implementation_per_subconfig[key] = "eager"

            config._attn_implementation = attn_implementation_per_subconfig
            model = model_class(config)
            for key in config.sub_configs:
                if getattr(config, key) is not None:
                    sub_config = getattr(model.config, key)
                    self.assertTrue(sub_config._attn_implementation == "eager")

            for name, submodule in model.named_modules():
                class_name = submodule.__class__.__name__
                if (
                    class_name.endswith("Attention")
                    and getattr(submodule, "config", None)
                    and submodule.config._attn_implementation != "eager"
                ):
                    raise ValueError(
                        f"The eager model should not have SDPA/FA2 attention layers but got `{class_name}.config._attn_implementation={submodule.config._attn_implementation}`"
                    )

            # Set the attention to default `None` but the text config to `eager`
            # The model should load encoders in SDPA but not the text attention
            config._attn_implementation = None
            config.get_text_config(decoder=True)._attn_implementation = "eager"
            model = model_class(config)
            self.assertTrue(model.config.get_text_config(decoder=True)._attn_implementation == "eager")

            # Test that using `dict` attention implementation works with `from_pretrained`
            #  Set all backbones to "eager" because "eager" attention is always available
            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                new_model = model.from_pretrained(tmpdirname, attn_implementation=attn_implementation_per_subconfig)
                self.assertTrue(new_model.config._attn_implementation == "eager")
                for submodule in new_model.modules():
                    if (
                        submodule is not new_model
                        and isinstance(submodule, PreTrainedModel)
                        and submodule.config.__class__ != new_model.config.__class__
                    ):
                        self.assertTrue(submodule.config._attn_implementation == "eager")
def test_can_set_attention_dynamically(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        for model_class in self.all_model_classes:
            if not model_class._can_set_attn_implementation():
                self.skipTest(reason="This model does not support setting its attention dynamically")

            # Need to deepcopy here to avoid changing the _attn_implementation in-place
            model_config = copy.deepcopy(config)
            # Set eager everywhere (it sets it recursively on subconfigs)
            model_config._attn_implementation = "eager"
            model = model_class(model_config)

            # sanity check to make sure everything is correctly eager
            self.assertTrue(model.config._attn_implementation == "eager")
            for subconfig_key in model.config.sub_configs:
                if getattr(config, subconfig_key) is not None:
                    self.assertTrue(getattr(model.config, subconfig_key)._attn_implementation == "eager")

            if not all(
                submodule._can_set_attn_implementation()
                for submodule in model.modules()
                if isinstance(submodule, PreTrainedModel)
            ):
                self.skipTest(reason="Parts of this model cannot set attention dynamically")
            # Some old models technically should support switching, but don't have the flags active...
            if not all(
                submodule._supports_sdpa for submodule in model.modules() if isinstance(submodule, PreTrainedModel)
            ):
                self.skipTest(reason="Parts of this model don't support sdpa")

            # Now, set it to sdpa
            model.set_attn_implementation("sdpa")

            # Check everything was correctly changed
            self.assertTrue(model.config._attn_implementation == "sdpa")
            for subconfig_key in model.config.sub_configs:
                if getattr(config, subconfig_key) is not None:
                    self.assertTrue(getattr(model.config, subconfig_key)._attn_implementation == "sdpa")

            # Check we cannot set it to random values, and it raises an error
            with self.assertRaisesRegex(ValueError, 'Specified `attn_implementation="foo"` is not supported'):
                model.set_attn_implementation("foo")

            # Should still be sdpa everywhere
            self.assertTrue(model.config._attn_implementation == "sdpa")
            for subconfig_key in model.config.sub_configs:
                if getattr(config, subconfig_key) is not None:
                    self.assertTrue(getattr(model.config, subconfig_key)._attn_implementation == "sdpa")
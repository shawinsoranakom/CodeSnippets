def test_internal_model_config_and_subconfig_are_same(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        subconfig_keys = list(config.sub_configs.keys())
        for model_class in self.all_model_classes:
            if len(config.sub_configs) == 0:
                self.skipTest(reason="No subconfigs so the test does not make sense")
            # Need to deepcopy here to avoid changing the _attn_implementation in-place
            model = model_class(copy.deepcopy(config))
            subconfig_keys_seen = set()

            for submodule in model.modules():
                # This is a submodel
                if isinstance(submodule, PreTrainedModel) and submodule.config.__class__ != model.config.__class__:
                    subconfig_from_model_internal = submodule.config
                    matching_sub_configs = []
                    for subconfig_key in subconfig_keys:
                        # Get the subconfig from the model config
                        subconfig_from_model_config = getattr(model.config, subconfig_key)
                        if (
                            subconfig_from_model_config is not None
                            and subconfig_from_model_config.__class__ == subconfig_from_model_internal.__class__
                            and subconfig_key not in subconfig_keys_seen
                        ):
                            # Since some composite models have different submodels parameterized by 2 of the same config
                            # class instances, we need to check against a list of matching classes, and check that at least
                            # 1 is the exact object (instead of checking immediately for similar object)
                            matching_sub_configs.append(subconfig_from_model_config)
                            subconfig_keys_seen.add(subconfig_key)

                    # Both should be exactly the same object, that is when instantiating the submodel when should
                    # absolutely not copy the subconfig
                    if len(matching_sub_configs) > 0:
                        self.assertTrue(
                            any(
                                subconfig_from_model_config is subconfig_from_model_internal
                                for subconfig_from_model_config in matching_sub_configs
                            )
                        )
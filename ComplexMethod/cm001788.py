def test_tp_plan_matches_params(self):
        """Make sure that each entry of the tp plan matches at least one param (this avoid typos and/or edge cases
        with regexes)"""
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        # If none of the config and subconfigs have a tp_plan, then skip (otherwise we should make sure to respect the plan)
        if config.base_model_tp_plan is None and all(
            getattr(getattr(config, key), "base_model_tp_plan", None) is None for key in config.sub_configs
        ):
            self.skipTest("Model does not have a TP plan.")

        # Some MoE models alternate between a classic MLP and a MoE layer, in which case we want to have each one
        # in order to test the whole tp plan
        config_to_set = config.get_text_config()
        config_to_set.first_k_dense_replace = 1  # means that the first layer (idx 0) will be MLP, then MoE
        config_to_set.moe_layer_start_index = 1  # same as above but for Ernie 4.5...
        config_to_set.mlp_only_layers = [0]  # same but for qwens

        for model_class in self.all_model_classes:
            model = model_class(copy.deepcopy(config))
            param_names = {name for name, _ in model.named_parameters()} | {name for name, _ in model.named_buffers()}
            module_names = {name for name, _ in model.named_modules()}
            tp_plan = model.tp_plan
            # Make sure the plan is not empty
            self.assertTrue(
                len(tp_plan) > 0,
                f"No TP-plan found for class {model_class.__name__} even though the associated config has one",
            )
            pattern_usage = {}
            for pattern in tp_plan:
                # Check if this given pattern matches any param or module (the value attributed to the pattern does not matter)
                pattern_usage[pattern] = any(
                    _get_parameter_tp_plan(param, {pattern: ""}, is_weight=True) is not None for param in param_names
                ) or any(
                    _get_parameter_tp_plan(module, {pattern: ""}, is_weight=False) is not None
                    for module in module_names
                )

            unused_entries = {k for k, v in pattern_usage.items() if not v}
            self.assertTrue(
                len(unused_entries) == 0, f"The following entries of the TP-plan are not valid: {unused_entries}"
            )
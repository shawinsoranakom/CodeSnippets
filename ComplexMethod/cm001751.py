def test_keep_in_fp32_modules_exist(self):
        """Test that both the `_keep_in_fp32` and `_keep_in_fp32_strict` targets match some layers, to avoid any typo"""
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        for model_class in self.all_model_classes:
            with self.subTest(model_class.__name__):
                model = model_class(copy.deepcopy(config))
                # Make sure the modules correctly exist if the flag is active
                if len(model._keep_in_fp32_modules) == 0 and len(model._keep_in_fp32_modules_strict) == 0:
                    self.skipTest(
                        reason=f"{model_class.__name__} has no _keep_in_fp32_modules nor _keep_in_fp32_modules_strict attribute defined"
                    )

                state_dict_names = {k for k, v in model.state_dict().items()}
                # Check that every module in the keep_in_fp32 list is part of the module graph
                if len(model._keep_in_fp32_modules) > 0:
                    non_existent = []
                    for module in model._keep_in_fp32_modules:
                        if not any(re.search(rf"(?:^|\.){module}(?:\.|$)", name) for name in state_dict_names):
                            non_existent.append(module)
                    self.assertTrue(
                        len(non_existent) == 0,
                        f"{non_existent} were specified in the `_keep_in_fp32_modules` list, but are not part of the modules in"
                        f" {model_class.__name__}",
                    )

                if len(model._keep_in_fp32_modules_strict) > 0:
                    non_existent = []
                    for module in model._keep_in_fp32_modules_strict:
                        if not any(re.search(rf"(?:^|\.){module}(?:\.|$)", name) for name in state_dict_names):
                            non_existent.append(module)
                    self.assertTrue(
                        len(non_existent) == 0,
                        f"{non_existent} were specified in the `_keep_in_fp32_modules_strict` list, but are not part of the "
                        f"modules in {model_class.__name__}",
                    )
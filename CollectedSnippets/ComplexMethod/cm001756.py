def test_can_init_all_missing_weights(self):
        """Ensure that all weights are correctly taken into account in `_init_weights`"""
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        # This is used to get the addition year of the model
        filename = inspect.getfile(config.__class__)
        # No easy way to get model addition date -> check copyright year on top of file
        with open(filename) as file:
            source_code = file.read()
        addition_year = 0  # if we cannot find it, set it to 0 (i.e. oldest)
        if match_object := re.search(r"^# Copyright (\d{4})", source_code, re.MULTILINE | re.IGNORECASE):
            addition_year = int(match_object.group(1))
        # For now, skip everything older than 2023 and "important models" (too many models to patch otherwise)
        # TODO: relax this as we patch more and more models
        if addition_year < 2023:
            self.skipTest(reason="Not a prioritized model for now.")

        for model_class in self.all_model_classes:
            # This context manager makes sure that we get the same results deterministically for random new weights
            with seeded_weight_init():
                # First, initialize the model from __init__ -> this ensure everything is correctly initialized, even if
                # _init_weights() does not take all weights into account correctly
                model_from_init = model_class(copy.deepcopy(config))
                # Here, passing an empty state dict will force all weights to be moved from meta to cpu, then be initialized
                # by _init_weights()
                model_from_pretrained = model_class.from_pretrained(None, config=copy.deepcopy(config), state_dict={})

            # First, check if any parameters/buffers are still on meta -> this is usually an issue with tied weights
            params_on_meta = []
            for k, v in model_from_pretrained.named_parameters():
                if v.device.type == "meta":
                    params_on_meta.append(k)
            for k, v in model_from_pretrained.named_buffers():
                if v.device.type == "meta":
                    params_on_meta.append(k)

            self.assertTrue(
                len(params_on_meta) == 0,
                f"The following keys are still on the meta device, it probably comes from an issue in the tied weights or buffers:\n{params_on_meta}",
            )

            from_pretrained_state_dict = model_from_pretrained.state_dict()
            from_init_state_dict = model_from_init.state_dict()
            self.assertEqual(
                sorted(from_pretrained_state_dict.keys()),
                sorted(from_init_state_dict.keys()),
                "The keys from each model should be the exact same",
            )

            # Everything must be exactly the same as we set the same seed for each init
            different_weights = set()
            for k1, v1 in from_init_state_dict.items():
                # In case using torch.nn.utils.parametrizations on a module, we should skip the resulting keys
                if re.search(r"\.parametrizations\..*?\.original[01]", k1):
                    continue
                v2 = from_pretrained_state_dict[k1]
                # Since we added the seed, they should be exactly the same (i.e. using allclose maybe be wrong due
                # to very low std in init function)
                if not (v1 == v2).all():
                    different_weights.add(k1)

            # Find the parent structure of the weights/buffers that are different for explicit error messages
            unique_bad_module_traceback = set()
            for weight in different_weights.copy():
                weight_name, immediate_parent_class, pretrained_parent_class = find_parent_traceback(
                    weight, model_from_init
                )

                # We cannot control timm model weights initialization, so skip in this case
                if (pretrained_parent_class == "TimmWrapperPreTrainedModel" and "timm_model." in weight) or (
                    pretrained_parent_class == "TimmBackbone" and "_backbone." in weight
                ):
                    different_weights.discard(weight)
                    continue

                # Add it to the traceback
                traceback = (
                    f"`{weight_name}` in module `{immediate_parent_class}` called from `{pretrained_parent_class}`\n"
                )
                unique_bad_module_traceback.add(traceback)

            self.assertTrue(
                len(different_weights) == 0,
                f"The following weights are not properly handled in `_init_weights()` (the model should be able to reinitialize "
                f"them correctly if the model is on meta device)::\n{unique_bad_module_traceback}",
            )
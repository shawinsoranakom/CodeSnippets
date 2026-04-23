def test_reverse_loading_mapping(self, check_keys_were_modified=True, skip_base_model=False):
        """Make sure we can load and save correctly the models having any weight renaming mapping or weight conversion
        mapping.
        Note that this test would be better if we could start from the serialized keys, and check that the model
        keys correspond to the weight converions. However, when instantiating a model, it already has the "target"
        keys (or modified keys after mapping) of the conversion mapping, so we have to do it the other way, i.e.
        reverse the conversion and then check that those converted keys match correctly the conversions.

        However, all the checks performed here should ensure everything is going as it should.

        Args:
            check_keys_were_modified (`bool`, *optional*, defaults to `True`):
                Whether to expect keys being modified or not. In some cases, models do not change keys but
                their weights, e.g. via transpose, memory alignment, etc.
            skip_base_model (`bool`, *optional*, defaults to `False`):
                Sometimes, mappings are only visible when applied to the model with head, and not visible on the
                base model. This allows to skip the check on the base model. See e.g. `llava` mapping where this
                is the case. In practice, the mappings are still coherent and a base model can still be loaded from
                the head model, thanks to the `base_model_prefix` which will remove the prefix automatically.
        """
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        #  Some MoE models alternate between a classic MLP and a MoE layer, in which case we want to have at
        # lest one MoE layer here to check the mapping
        config_to_set = config.get_text_config(decoder=True)
        config_to_set.first_k_dense_replace = 1  # means that the first layer (idx 0) will be MLP, then MoE
        config_to_set.moe_layer_start_index = 1  # same as above but for Ernie 4.5...
        config_to_set.mlp_only_layers = [0]  # same but for qwens
        config_to_set.num_dense_layers = 1  # lfm2_moe

        for model_class in self.all_model_classes:
            if skip_base_model and "For" not in model_class.__name__:
                continue
            # Each individual model is a subtest
            with self.subTest(model_class.__name__):
                model = model_class(copy.deepcopy(config))
                # Skip if no conversions
                conversions = get_model_conversion_mapping(model, add_legacy=False)
                if len(conversions) == 0:
                    self.skipTest(f"No conversion found for {model_class}")
                # The PrefixChange conersions are only there for BC with hub checkpoints, but cannot be tested
                # for as we skip them automatically if they are not present in loaded checkpoints (we want to
                # mess up the prefixes only if the loaded checkpoints were doing so as well)
                if all(isinstance(conversion, PrefixChange) for conversion in conversions):
                    self.skipTest(f"Only PrefixChange conversions found for {model_class}")

                # Find the model keys, so the targets according to the conversions
                model_keys = list(model.state_dict().keys())

                with tempfile.TemporaryDirectory() as tmpdirname:
                    # Serialize with reverse mapping
                    model.save_pretrained(tmpdirname)
                    state_dict = load_file(os.path.join(tmpdirname, "model.safetensors"))
                    # Get all the serialized keys that we just saved according to the reverse mapping
                    serialized_keys = list(state_dict.keys())

                if check_keys_were_modified:
                    # They should be different, otherwise we did not perform any mapping
                    self.assertNotEqual(sorted(serialized_keys), sorted(model_keys), "No key mapping was performed!")

                # Check that for each conversion entry, we at least map to one key
                for conversion in conversions:
                    # The PrefixChange conersions are only there for BC with hub checkpoints, but cannot be tested
                    # for as we skip them automatically if they are not present in loaded checkpoints (we want to
                    # mess up the prefixes only if the loaded checkpoints were doing so as well)
                    if isinstance(conversion, PrefixChange):
                        continue
                    for source_pattern in conversion.source_patterns:
                        # Some patterns are written for gen-model only and won't be applied on base model
                        if "lm_head" in source_pattern and model_class not in [
                            *get_values(MODEL_FOR_CAUSAL_LM_MAPPING_NAMES),
                            *get_values(MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES),
                        ]:
                            continue

                        # Sometimes the mappings specify keys that are tied, so absent from the saved state dict
                        if isinstance(conversion, WeightRenaming):
                            # We need to revert the target pattern to make it compatible with regex search
                            target_pattern_reversed = conversion.target_patterns[0]
                            captured_group = process_target_pattern(source_pattern)[1]
                            if captured_group:
                                target_pattern_reversed = target_pattern_reversed.replace(r"\1", captured_group)
                            if any(re.search(target_pattern_reversed, k) for k in model.all_tied_weights_keys.keys()):
                                continue
                        num_matches = sum(re.search(source_pattern, key) is not None for key in serialized_keys)
                        self.assertTrue(
                            num_matches > 0,
                            f"`{source_pattern}` in `{conversion}` did not match any of the source keys. "
                            "This indicates whether that the pattern is not properly written, or that it could not be reversed correctly",
                        )

                # If everything is still good at this point, let's test that we perform the same operations both when
                # reverting ops from `from_pretrained` and from `__init__`
                with tempfile.TemporaryDirectory() as tmpdirname:
                    # The model was instantiated from __init__ before being saved
                    model.save_pretrained(tmpdirname)
                    state_dict_saved_from_init = load_file(os.path.join(tmpdirname, "model.safetensors"))

                    # Now reload it
                    model_reloaded = model_class.from_pretrained(tmpdirname)

                    # Make sure both loaded state_dict are identical
                    self.assertTrue(compare_state_dicts(model_reloaded.state_dict(), model.state_dict()))

                    # The model was instantiated from `from_pretrained` before being saved
                    model_reloaded.save_pretrained(tmpdirname)
                    state_dict_saved_from_pretrained = load_file(os.path.join(tmpdirname, "model.safetensors"))

                    # Make sure both saved state_dict are identical
                    self.assertTrue(compare_state_dicts(state_dict_saved_from_init, state_dict_saved_from_pretrained))
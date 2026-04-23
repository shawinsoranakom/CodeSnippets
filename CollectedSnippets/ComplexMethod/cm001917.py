def test_tied_weights_keys(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        config.tie_word_embeddings = True
        for model_class in self.all_model_classes:
            model_tied = model_class(config)

            ptrs = collections.defaultdict(list)
            for name, tensor in model_tied.state_dict().items():
                ptrs[id_tensor_storage(tensor)].append(name)

            # These are all the pointers of shared tensors.
            tied_params = [names for _, names in ptrs.items() if len(names) > 1]

            tied_weight_keys = model_tied._tied_weights_keys if model_tied._tied_weights_keys is not None else []
            # Detect we get a hit for each key
            for key in tied_weight_keys:
                if not any(re.search(key, p) for group in tied_params for p in group):
                    raise ValueError(f"{key} is not a tied weight key for {model_class}.")

            # Removed tied weights found from tied params -> there should only be one left after
            for key in tied_weight_keys:
                for i in range(len(tied_params)):
                    tied_params[i] = [p for p in tied_params[i] if re.search(key, p) is None]

            # MMGroundingDino when sharing weights also uses the shared ones in MMGroundingDinoDecoder
            # Therefore, differently from DeformableDetr, we expect the group lens to be 2
            # one for self.bbox_embed in MMGroundingDinoForObjectDetection and another one
            # in the decoder
            tied_params = [group for group in tied_params if len(group) > 2]
            self.assertListEqual(
                tied_params,
                [],
                f"Missing `_tied_weights_keys` for {model_class}: add all of {tied_params} except one.",
            )
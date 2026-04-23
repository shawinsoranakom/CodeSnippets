def test_tied_weights_keys(self):
        original_config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        for model_class in self.all_model_classes:
            copied_config = copy.deepcopy(original_config)
            copied_config.get_text_config().tie_word_embeddings = True
            copied_config.tie_word_embeddings = True
            model_tied = model_class(copied_config)

            tied_weight_keys = _get_tied_weight_keys(model_tied)
            # If we don't find any tied weights keys, and by default we don't tie the embeddings, it's because the model
            # does not tie them or does not have embedding layer (non-text model)
            if len(tied_weight_keys) == 0 and not getattr(original_config, "tie_word_embeddings", None):
                continue

            ptrs = collections.defaultdict(list)
            for name, tensor in model_tied.state_dict().items():
                ptrs[id_tensor_storage(tensor)].append(name)

            # These are all the pointers of shared tensors.
            tied_params = [names for _, names in ptrs.items() if len(names) > 1]

            # Detect we get a hit for each key
            for key in tied_weight_keys:
                is_tied_key = any(re.search(key, p) for group in tied_params for p in group)
                self.assertTrue(
                    is_tied_key,
                    f"{key} is not a tied weight key pattern for {model_class}: {is_tied_key}. With same params: {tied_params}",
                )

            # Removed tied weights found from tied params -> there should only be one left after
            for key in tied_weight_keys:
                for i in range(len(tied_params)):
                    tied_params[i] = [p for p in tied_params[i] if re.search(key, p) is None]

            tied_params = [group for group in tied_params if len(group) > 1]
            self.assertListEqual(
                tied_params,
                [],
                f"Missing `_tied_weights_keys` for {model_class}: add all of {tied_params} except one.",
            )
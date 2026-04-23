def test_model_forward_default_config_values(
        self,
    ):
        """
        Tests that the model can run forward pass when config is intialized without common attributes.
        We expect that these attributes have a default value and will not cause errors. See #41541
        where the attributes were removed from `PreTrainedConfig` and moved to each model's config
        class.
        """
        common_config_properties = [
            "pad_token_id",
            "eos_token_id",
            "bos_token_id",
            "sep_token_id",
            "tie_word_embeddings",
        ]
        config, batched_input = self.model_tester.prepare_config_and_inputs_for_common()
        batch_size = self.model_tester.batch_size

        config_dict = config.to_diff_dict()
        for common_config_property in common_config_properties:
            config_dict.pop(common_config_property, None)
            for subconfig_key in config.sub_configs:
                subconfig = config_dict.get(subconfig_key, {})
                if subconfig:
                    subconfig.pop(common_config_property, None)
        config = config.__class__(**config_dict)

        # Set special tokens to `0` so it is guaranteed to be in vocab range
        for special_token in ["pad_token_id", "eos_token_id", "bos_token_id", "sep_token_id"]:
            if hasattr(config, special_token):
                setattr(config, special_token, 0)
            for subconfig_key in config.sub_configs:
                subconfig = getattr(config, subconfig_key, None)
                if subconfig and hasattr(subconfig, special_token):
                    setattr(subconfig, special_token, 0)

        for model_class in self.all_model_classes:
            if model_class.__name__ not in [
                *get_values(MODEL_MAPPING_NAMES),
            ]:
                continue

            model = model_class(copy.deepcopy(config)).to(torch_device).eval()
            single_batch_input = {}
            for key, value in batched_input.items():
                if isinstance(value, torch.Tensor) and value.shape[0] % batch_size == 0:
                    # e.g. musicgen has inputs of size (bs*codebooks). in most cases value.shape[0] == batch_size
                    single_batch_shape = value.shape[0] // batch_size
                    single_batch_input[key] = value[:single_batch_shape]
                else:
                    single_batch_input[key] = value

            with torch.no_grad():
                model(**single_batch_input)
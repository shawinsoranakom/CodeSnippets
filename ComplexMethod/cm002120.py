def test_rope_validation(self):
        config = LlamaConfig()
        all_rope_types = ROPE_INIT_FUNCTIONS.keys()

        # The base config is always valid (default RoPE)
        config.validate_rope()

        # If we explicitly set the other (non-default) RoPE types with only rope_theta,
        # validation should fail because required keys are missing (e.g. factor, short_factor)
        for rope_type in all_rope_types:
            if rope_type == "default":
                continue  # "default" is always valid with just rope_theta
            # proportional is same as default wrt to expected keys
            if rope_type == "proportional":
                continue
            config.rope_parameters = {"rope_type": rope_type, "rope_theta": 10000.0}
            with self.assertRaises(KeyError):
                config.validate_rope()

        # Parameters are exclusive to their own RoPE type, and should raise an exception if incorrectly passed
        valid_param_mapping = {
            "factor": ["linear", "dynamic", "yarn", "longrope"],
            "attention_factor": ["yarn", "longrope"],
            "beta_fast": ["yarn"],
            "beta_slow": ["yarn"],
            "short_factor": ["longrope"],
            "long_factor": ["longrope"],
        }
        for rope_type in all_rope_types:
            if rope_type == "default":
                continue  # "default" only warns about unrecognised keys, never raises KeyError
            # proportional is same as default wrt to expected keys
            if rope_type == "proportional":
                continue
            for param, valid_rope_types in valid_param_mapping.items():
                # Set `param` with a dummy value -- we want to test the dict key
                config.rope_parameters = {"rope_type": rope_type, "rope_theta": 10000.0, param: True}
                if rope_type in valid_rope_types:
                    continue
                else:
                    with self.assertRaises(KeyError):
                        config.validate_rope()

        # Any other parameters passed to RoPE will raise a warning that a particular key is not used
        # But sometimes we can have model-specific RoPE kwargs and bypass warning with `ignore_keys`
        config.ignore_keys_at_rope_validation = {"mrope_sections"}  # e,g in Qwen2-VL
        config.rope_parameters = {"rope_type": "default", "rope_theta": 10000.0, "mrope_sections": True}
        config.validate_rope()

        with self.assertLogs("transformers.modeling_rope_utils", level="WARNING") as logs:
            config.ignore_keys_at_rope_validation = set()
            config.validate_rope()
            self.assertEqual(len(logs.output), 1)
            self.assertIn("mrope_sections", logs.output[0])

        # We can indicate Different RoPE params for each attention type
        # We can also have only one RoPE params defined for all layer, we don't raise an error
        # because it is not required to have separate RoPE per layer type
        config.layer_types = ["full_attention", "sliding_attention"]
        config.rope_parameters = {
            "full_attention": {"rope_type": "default", "rope_theta": 10000},
            "sliding_attention": {"rope_type": "linear", "rope_theta": 10000, "factor": 2.0},
        }
        config.validate_rope()

        config.rope_parameters = config.rope_parameters["full_attention"]
        config.validate_rope()
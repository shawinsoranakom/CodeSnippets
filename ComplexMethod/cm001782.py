def test_sliding_window_mask(self):
        """Tests that we can control the sliding window attention behavior of a model."""
        config, inputs = self.model_tester.prepare_config_and_inputs_for_common()

        if not self.has_attentions:
            self.skipTest(reason="Model does not support output_attentions")

        if not (hasattr(config, "sliding_window") and hasattr(config, "use_sliding_window")):
            self.skipTest(reason="Model does not support sliding window mask")

        seq_len = self.model_tester.seq_length
        batch_size = self.model_tester.batch_size
        sliding_window = 3  # set to arbitrary small number

        sliding_mask = torch.zeros((seq_len, seq_len), dtype=torch.bool)
        for i in range(seq_len):
            start = max(0, i - sliding_window + 1)
            sliding_mask[i, start : i + 1] = True
        sliding_mask = sliding_mask.to(torch_device)

        config.sliding_window = sliding_window
        inputs["attention_mask"] = torch.ones(batch_size, seq_len).to(torch.int64).to(torch_device)
        for model_class in self.all_model_classes:
            # Set sliding window to `True` and check that all tokens beyond window size are masked
            config.use_sliding_window = True
            config_dict = config.to_diff_dict()
            config_dict.pop("layer_types", None)
            config_dict.pop("rope_parameters", None)
            new_config = config.__class__(**config_dict)
            # We need to set eager as otherwise `output_attentions` is not supported
            model = model_class._from_config(new_config, attn_implementation="eager").to(torch_device)
            model.eval()
            layer_types = getattr(model.config, "layer_types", ["sliding_attention"] * config.num_hidden_layers)
            attentions = model(**inputs, output_attentions=True).attentions
            for layer_attention, layer_type in zip(attentions, layer_types):
                if layer_type == "sliding_attention":
                    self.assertTrue((layer_attention[:, :, ~sliding_mask] == 0).all().item())
                else:
                    self.assertFalse((layer_attention[:, :, ~sliding_mask] == 0).all().item())

            # Set sliding window to `False` while keeping `sliding_window=3`
            # Check that all tokens beyond window size are not masked
            config.use_sliding_window = False
            config_dict = config.to_diff_dict()
            config_dict.pop("layer_types", None)
            config_dict.pop("rope_parameters", None)
            new_config = config.__class__(**config_dict)
            # We need to set eager as otherwise `output_attentions` is not supported
            model = model_class._from_config(new_config, attn_implementation="eager").to(torch_device)
            model.eval()
            attentions_not_sliding = model(**inputs, output_attentions=True).attentions
            for layer_attention in attentions_not_sliding:
                self.assertFalse((layer_attention[:, :, ~sliding_mask] == 0).all().item())
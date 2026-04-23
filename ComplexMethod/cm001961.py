def test_attention_mask_with_token_types(self):
        """Test that attention masking works correctly both with and without token type IDs."""
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class._from_config(config, attn_implementation="eager")
            config = model.config
            model.to(torch_device)
            model.eval()

            # Case 1: With token_type_ids
            outputs_with_types = model(
                **inputs_dict,
                output_attentions=True,
            )

            # Case 2: Without token_type_ids
            inputs_no_types = {k: v for k, v in inputs_dict.items() if k != "token_type_ids"}
            outputs_no_types = model(
                **inputs_no_types,
                output_attentions=True,
            )

            attention_outputs_with_types = outputs_with_types.attentions
            attention_outputs_no_types = outputs_no_types.attentions

            # Verify pad tokens remain masked in both cases
            attention_mask = inputs_dict["attention_mask"]
            pad_positions = attention_mask == 0

            for layer_attentions in [attention_outputs_with_types, attention_outputs_no_types]:
                for layer_attn in layer_attentions:
                    # Check if pad tokens are properly masked
                    for batch_idx in range(layer_attn.shape[0]):
                        for seq_idx in range(layer_attn.shape[-1]):
                            if pad_positions[batch_idx, seq_idx]:
                                # Verify attention weights for pad tokens are zero
                                self.assertTrue(
                                    torch.all(layer_attn[batch_idx, :, :, seq_idx] == 0),
                                    f"Found non-zero attention weights for padding token at batch {batch_idx}, sequence position {seq_idx}",
                                )
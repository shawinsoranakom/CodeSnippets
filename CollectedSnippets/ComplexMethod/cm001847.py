def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        """Override to ensure input_ids and attention_mask are always present for Sam3Model."""
        inputs_dict = super()._prepare_for_class(inputs_dict, model_class, return_labels=return_labels)

        # Sam3Model always requires input_ids and attention_mask for text encoding
        if model_class == Sam3Model:
            if "input_ids" not in inputs_dict or inputs_dict.get("input_ids") is None:
                # Create dummy input_ids if not present
                # Get batch_size from pixel_values or vision_embeds
                if "pixel_values" in inputs_dict and inputs_dict.get("pixel_values") is not None:
                    batch_size = inputs_dict["pixel_values"].shape[0]
                elif "vision_embeds" in inputs_dict and inputs_dict.get("vision_embeds") is not None:
                    vision_embeds = inputs_dict["vision_embeds"]
                    if vision_embeds.fpn_hidden_states is not None and len(vision_embeds.fpn_hidden_states) > 0:
                        batch_size = vision_embeds.fpn_hidden_states[0].shape[0]
                    elif vision_embeds.last_hidden_state is not None:
                        batch_size = vision_embeds.last_hidden_state.shape[0]
                    else:
                        batch_size = 2
                else:
                    batch_size = 2
                config = self.model_tester.get_config()
                # text_config might be a dict or a config object
                if isinstance(config.text_config, dict):
                    vocab_size = config.text_config.get("vocab_size", 1000)
                else:
                    vocab_size = getattr(config.text_config, "vocab_size", 1000)
                inputs_dict["input_ids"] = torch.randint(0, vocab_size, (batch_size, 16), device=torch_device)
            if "attention_mask" not in inputs_dict or inputs_dict.get("attention_mask") is None:
                inputs_dict["attention_mask"] = torch.ones_like(inputs_dict["input_ids"])

        return inputs_dict
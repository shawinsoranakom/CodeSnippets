def prepare_inputs_for_generation(
        self,
        input_ids,
        attention_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        past_key_values=None,
        use_cache=True,
        delay_pattern_mask=None,
        guidance_scale=None,
        **kwargs,
    ):
        # Overwritten -- MusicGen has custom processing
        if delay_pattern_mask is None:
            input_ids, delay_pattern_mask = self.build_delay_pattern_mask(
                input_ids,
                pad_token_id=self.generation_config.pad_token_id,
                max_length=self.generation_config.max_length,
            )

        # apply the delay pattern mask
        input_ids = self.apply_delay_pattern_mask(input_ids, delay_pattern_mask)

        if guidance_scale is not None and guidance_scale > 1:
            # for classifier free guidance we need to replicate the decoder args across the batch dim (we'll split these
            # before sampling)
            input_ids = input_ids.repeat((2, 1))
            if attention_mask is not None:
                attention_mask = attention_mask.repeat((2, 1))

            if encoder_hidden_states is not None:
                encoder_hidden_states = torch.concatenate(
                    [encoder_hidden_states, torch.zeros_like(encoder_hidden_states)], dim=0
                )

            if encoder_attention_mask is not None:
                encoder_attention_mask = torch.concatenate(
                    encoder_attention_mask, torch.zeros_like(encoder_attention_mask), dim=0
                )

        if past_key_values is not None:
            input_ids = input_ids[:, -1:]

            # we only want to use conditional signal in the 1st generation step but keeping the attention mask
            encoder_hidden_states = None

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "encoder_hidden_states": encoder_hidden_states,
            "encoder_attention_mask": encoder_attention_mask,
            "past_key_values": past_key_values,
            "use_cache": use_cache,
        }
def generate(
        self,
        pixel_values: torch.FloatTensor,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        interpolate_pos_encoding: bool = False,
        **generate_kwargs,
    ) -> torch.LongTensor:
        """
        Overrides `generate` function to be able to use the model as a conditional generator.

        Args:
            pixel_values (`torch.FloatTensor` of shape (batch_size, num_channels, height, width)):
                Input images to be processed.
            input_ids (`torch.LongTensor` of shape (batch_size, sequence_length), *optional*):
                The sequence used as a prompt for the generation.
            attention_mask (`torch.LongTensor` of shape (batch_size, sequence_length), *optional*):
                Mask to avoid performing attention on padding token indices
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Embedded representation of the inputs. Should be float, not int tokens.
            interpolate_pos_encoding (`bool`, *optional*, defaults to `False`):
                Whether to interpolate the positional encoding of the image embeddings.

        Returns:
            captions (list): A list of strings of length batch_size * num_captions.
        """
        if hasattr(self, "hf_device_map"):
            # preprocess for `accelerate`
            self._preprocess_accelerate()

        batch_size = pixel_values.shape[0]
        image_embeds = self.vision_model(
            pixel_values,
            return_dict=True,
            interpolate_pos_encoding=interpolate_pos_encoding,
        ).last_hidden_state
        image_attention_mask = torch.ones(image_embeds.size()[:-1], dtype=torch.long, device=image_embeds.device)

        query_tokens = self.query_tokens.expand(image_embeds.shape[0], -1, -1)
        query_outputs = self.qformer(
            query_embeds=query_tokens,
            encoder_hidden_states=image_embeds,
            encoder_attention_mask=image_attention_mask,
            return_dict=True,
        )
        query_output = query_outputs.last_hidden_state

        # Qformer is kept in fp32, we downcast the output back if needed
        if query_output.dtype != image_embeds.dtype:
            query_output = query_output.to(image_embeds.dtype)

        language_model_inputs = self.language_projection(query_output)

        if inputs_embeds is None:
            if input_ids is None:
                image_tokens = [self.config.image_token_index] * self.config.num_query_tokens
                start_tokens = image_tokens + [self.config.text_config.bos_token_id]
                input_ids = torch.tensor([start_tokens], dtype=torch.long, device=image_embeds.device)
                input_ids = input_ids.repeat(batch_size, 1)
            inputs_embeds = self.get_input_embeddings()(input_ids)

        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        if input_ids is None:
            special_image_mask = inputs_embeds == self.get_input_embeddings()(
                torch.tensor(self.config.image_token_id, dtype=torch.long, device=inputs_embeds.device)
            )
            special_image_mask = special_image_mask.all(-1)
        else:
            special_image_mask = input_ids == self.config.image_token_id

        special_image_mask = special_image_mask.unsqueeze(-1).expand_as(inputs_embeds).to(inputs_embeds.device)
        language_model_inputs = language_model_inputs.to(inputs_embeds.device, inputs_embeds.dtype)
        inputs_embeds = inputs_embeds.masked_scatter(special_image_mask, language_model_inputs)

        inputs = {"inputs_embeds": inputs_embeds, "attention_mask": attention_mask}
        if not self.language_model.config.is_encoder_decoder:
            inputs["input_ids"] = input_ids

        outputs = self.language_model.generate(**inputs, **generate_kwargs)

        return outputs
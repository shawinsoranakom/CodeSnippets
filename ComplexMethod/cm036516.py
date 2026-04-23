def patched_forward(
        self,
        input_ids=None,
        tensor_stream=None,
        attention_mask=None,
        position_ids=None,
        modality_tensor=None,
        past_key_values=None,
        inputs_embeds=None,
        use_cache=None,
        output_hidden_states=None,
        return_dict=None,
        cache_position=None,
        **kwargs,
    ):
        """
        Forward pass with MRoPE position embeddings.
        Computes position embeddings once and passes them through all layers.
        """
        output_hidden_states = (
            output_hidden_states
            if output_hidden_states is not None
            else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = (
            return_dict if return_dict is not None else self.config.use_return_dict
        )

        # Get inputs
        if tensor_stream is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both tensor_stream and inputs_embeds")
        elif tensor_stream is not None:
            # Embed TensorStream directly
            inputs_embeds = self.embed_stream(tensor_stream)
            # Create modality tensor if not provided
            if modality_tensor is None:
                modality_tensor = modality_mask(tensor_stream)
        elif input_ids is not None and inputs_embeds is not None:
            raise ValueError(
                "You cannot specify both input_ids and inputs_embeds at the same time"
            )
        elif input_ids is not None:
            inputs_embeds = self.embed_tokens(input_ids)
            # Create text modality tensor if not provided
            if modality_tensor is None:
                batch_size, seq_length = input_ids.shape
                modality_tensor = torch.full(
                    (batch_size, seq_length),
                    TextType.text.value,
                    device=input_ids.device,
                    dtype=torch.long,
                )
        elif inputs_embeds is None:
            raise ValueError(
                "You have to specify either tensor_stream, input_ids or inputs_embeds"
            )

        # Create default position_ids if not provided
        if position_ids is None:
            if tensor_stream is not None:
                position_ids = compute_mrope_pos_tensor(tensor_stream)  # (B,L,3)
            else:
                position_ids = compute_position_ids_input_ids(input_ids)

        # Compute MRoPE position embeddings if we have custom rotary_emb
        cos, sin = self.rotary_emb(position_ids, modality_tensor)
        cos = cos.to(inputs_embeds.dtype)
        sin = sin.to(inputs_embeds.dtype)

        # Prepare attention mask
        attention_mask = create_causal_mask(
            config=self.config,
            input_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
            cache_position=cache_position,
        )

        # Initialize and collect hidden states
        hidden_states = inputs_embeds
        hidden_states_list: list[torch.Tensor] = []

        if output_hidden_states:
            hidden_states_list.append(hidden_states)

        for decoder_layer in self.layers:
            layer_outputs = decoder_layer(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_key_values,
                use_cache=use_cache,
                cache_position=cache_position,
                position_embeddings=(cos, sin),
                **kwargs,
            )

            hidden_states = (
                layer_outputs[0] if isinstance(layer_outputs, tuple) else layer_outputs
            )

            if output_hidden_states:
                hidden_states_list.append(hidden_states)

        # Final layer norm
        hidden_states = self.norm(hidden_states)

        if output_hidden_states:
            hidden_states_list.append(hidden_states)

        # Convert to tuple or None
        all_hidden_states = tuple(hidden_states_list) if output_hidden_states else None

        # Include hidden_states for compatibility with hidden_states_to_seq_logprobs()
        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
            hidden_states=all_hidden_states,
        )
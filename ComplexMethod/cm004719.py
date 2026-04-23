def forward(
        self,
        inputs_embeds,
        encoder_hidden_states,
        memory_key_padding_mask,
        object_queries,
        query_position_embeddings,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ):
        r"""
        Args:
            inputs_embeds (`torch.FloatTensor` of shape `(sequence_length, batch_size, hidden_size)`):
                The query embeddings that are passed into the decoder.
            encoder_hidden_states (`torch.FloatTensor` of shape `(encoder_sequence_length, batch_size, hidden_size)`, *optional*):
                Sequence of hidden-states at the output of the last layer of the encoder. Used in the cross-attention
                of the decoder.
            memory_key_padding_mask (`torch.Tensor.bool` of shape `(batch_size, sequence_length)`):
                The memory_key_padding_mask indicates which positions in the memory (encoder outputs) should be ignored during the attention computation,
                ensuring padding tokens do not influence the attention mechanism.
            object_queries (`torch.FloatTensor` of shape `(sequence_length, batch_size, hidden_size)`, *optional*):
                Position embeddings that are added to the queries and keys in each cross-attention layer.
            query_position_embeddings (`torch.FloatTensor` of shape `(num_queries, batch_size, number_of_anchor_points)`):
                Position embeddings that are added to the queries and keys in each self-attention layer.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors
                for more detail.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if inputs_embeds is not None:
            hidden_states = inputs_embeds

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        all_cross_attentions = () if (output_attentions and encoder_hidden_states is not None) else None

        intermediate = []
        reference_points = query_position_embeddings.sigmoid()
        ref_points = [reference_points]

        # expand encoder attention mask
        if encoder_hidden_states is not None and memory_key_padding_mask is not None:
            memory_key_padding_mask = create_bidirectional_mask(
                config=self.config,
                inputs_embeds=inputs_embeds,
                attention_mask=memory_key_padding_mask,
                encoder_hidden_states=encoder_hidden_states,
            )

        for layer_id, decoder_layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            obj_center = reference_points[..., : self.config.query_dim]
            query_sine_embed = gen_sine_position_embeddings(obj_center, self.hidden_size)
            query_pos = self.ref_point_head(query_sine_embed)

            # For the first decoder layer, we do not apply transformation over p_s
            pos_transformation = 1 if layer_id == 0 else self.query_scale(hidden_states)

            # apply transformation
            query_sine_embed = query_sine_embed[..., : self.hidden_size] * pos_transformation

            # modulated Height Width attentions
            reference_anchor_size = self.ref_anchor_head(hidden_states).sigmoid()  # nq, bs, 2
            query_sine_embed[..., self.hidden_size // 2 :] *= (
                reference_anchor_size[..., 0] / obj_center[..., 2]
            ).unsqueeze(-1)
            query_sine_embed[..., : self.hidden_size // 2] *= (
                reference_anchor_size[..., 1] / obj_center[..., 3]
            ).unsqueeze(-1)

            layer_outputs = decoder_layer(
                hidden_states,
                None,  # attention_mask
                object_queries,
                query_pos,
                query_sine_embed,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=memory_key_padding_mask,
                output_attentions=output_attentions,
            )

            # iter update
            hidden_states = layer_outputs[0]

            if self.bbox_embed is not None:
                new_reference_points = self.bbox_embed(hidden_states)

                new_reference_points[..., : self.config.query_dim] += inverse_sigmoid(reference_points)
                new_reference_points = new_reference_points[..., : self.config.query_dim].sigmoid()
                if layer_id != self.num_layers - 1:
                    ref_points.append(new_reference_points)
                reference_points = new_reference_points.detach()

            intermediate.append(self.layernorm(hidden_states))

            if output_attentions:
                all_self_attns += (layer_outputs[1],)

                if encoder_hidden_states is not None:
                    all_cross_attentions += (layer_outputs[2],)

        # Layer normalization on hidden states
        hidden_states = self.layernorm(hidden_states)

        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        output_intermediate_hidden_states = torch.stack(intermediate)
        output_reference_points = torch.stack(ref_points)

        if not return_dict:
            return tuple(
                v
                for v in [
                    hidden_states,
                    all_hidden_states,
                    all_self_attns,
                    all_cross_attentions,
                    output_intermediate_hidden_states,
                    output_reference_points,
                ]
                if v is not None
            )
        return DabDetrDecoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attns,
            cross_attentions=all_cross_attentions,
            intermediate_hidden_states=output_intermediate_hidden_states,
            reference_points=output_reference_points,
        )
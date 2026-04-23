def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | CanineModelOutputWithPooling:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            self.warn_if_padding_and_no_attention_mask(input_ids, attention_mask)
            input_shape = input_ids.size()
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        batch_size, seq_length = input_shape
        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if attention_mask is None:
            attention_mask = torch.ones(((batch_size, seq_length)), device=device)
        if token_type_ids is None:
            token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=device)

        # We can provide a self-attention mask of dimensions [batch_size, from_seq_length, to_seq_length]
        # ourselves in which case we just need to make it broadcastable to all heads.
        extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(attention_mask, input_shape)
        molecule_attention_mask = self._downsample_attention_mask(
            attention_mask, downsampling_rate=self.config.downsampling_rate
        )
        extended_molecule_attention_mask: torch.Tensor = self.get_extended_attention_mask(
            molecule_attention_mask, (batch_size, molecule_attention_mask.shape[-1])
        )

        # `input_char_embeddings`: shape (batch_size, char_seq, char_dim)
        input_char_embeddings = self.char_embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
        )

        # Contextualize character embeddings using shallow Transformer.
        # We use a 3D attention mask for the local attention.
        # `input_char_encoding`: shape (batch_size, char_seq_len, char_dim)
        char_attention_mask = self._create_3d_attention_mask_from_input_mask(
            input_ids if input_ids is not None else inputs_embeds, attention_mask
        )
        init_chars_encoder_outputs = self.initial_char_encoder(
            input_char_embeddings,
            attention_mask=char_attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )
        input_char_encoding = init_chars_encoder_outputs.last_hidden_state

        # Downsample chars to molecules.
        # The following lines have dimensions: [batch, molecule_seq, molecule_dim].
        # In this transformation, we change the dimensionality from `char_dim` to
        # `molecule_dim`, but do *NOT* add a resnet connection. Instead, we rely on
        # the resnet connections (a) from the final char transformer stack back into
        # the original char transformer stack and (b) the resnet connections from
        # the final char transformer stack back into the deep BERT stack of
        # molecules.
        #
        # Empirically, it is critical to use a powerful enough transformation here:
        # mean pooling causes training to diverge with huge gradient norms in this
        # region of the model; using a convolution here resolves this issue. From
        # this, it seems that molecules and characters require a very different
        # feature space; intuitively, this makes sense.
        init_molecule_encoding = self.chars_to_molecules(input_char_encoding)

        # Deep BERT encoder
        # `molecule_sequence_output`: shape (batch_size, mol_seq_len, mol_dim)
        encoder_outputs = self.encoder(
            init_molecule_encoding,
            attention_mask=extended_molecule_attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        molecule_sequence_output = encoder_outputs[0]
        pooled_output = self.pooler(molecule_sequence_output) if self.pooler is not None else None

        # Upsample molecules back to characters.
        # `repeated_molecules`: shape (batch_size, char_seq_len, mol_hidden_size)
        repeated_molecules = self._repeat_molecules(molecule_sequence_output, char_seq_length=input_shape[-1])

        # Concatenate representations (contextualized char embeddings and repeated molecules):
        # `concat`: shape [batch_size, char_seq_len, molecule_hidden_size+char_hidden_final]
        concat = torch.cat([input_char_encoding, repeated_molecules], dim=-1)

        # Project representation dimension back to hidden_size
        # `sequence_output`: shape (batch_size, char_seq_len, hidden_size])
        sequence_output = self.projection(concat)

        # Apply final shallow Transformer
        # `sequence_output`: shape (batch_size, char_seq_len, hidden_size])
        final_chars_encoder_outputs = self.final_char_encoder(
            sequence_output,
            attention_mask=extended_attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )
        sequence_output = final_chars_encoder_outputs.last_hidden_state

        if output_hidden_states:
            deep_encoder_hidden_states = encoder_outputs.hidden_states if return_dict else encoder_outputs[1]
            all_hidden_states = (
                all_hidden_states
                + init_chars_encoder_outputs.hidden_states
                + deep_encoder_hidden_states
                + final_chars_encoder_outputs.hidden_states
            )

        if output_attentions:
            deep_encoder_self_attentions = encoder_outputs.attentions if return_dict else encoder_outputs[-1]
            all_self_attentions = (
                all_self_attentions
                + init_chars_encoder_outputs.attentions
                + deep_encoder_self_attentions
                + final_chars_encoder_outputs.attentions
            )

        if not return_dict:
            output = (sequence_output, pooled_output)
            output += tuple(v for v in [all_hidden_states, all_self_attentions] if v is not None)
            return output

        return CanineModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )
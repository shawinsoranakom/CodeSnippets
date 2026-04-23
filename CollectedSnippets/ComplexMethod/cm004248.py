def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        encoder_outputs: tuple[tuple[torch.Tensor]] | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        output_router_logits: bool | None = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.FloatTensor] | Seq2SeqMoEOutput:
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                inputs_embeds=inputs_embeds,
                output_router_logits=output_router_logits,
                **kwargs,
            )

        hidden_states = encoder_outputs[0]

        if labels is not None and decoder_input_ids is None and decoder_inputs_embeds is None:
            # get decoder inputs from shifting lm labels to the right
            decoder_input_ids = self._shift_right(labels)

        # Decode
        decoder_outputs = self.decoder(
            input_ids=decoder_input_ids,
            attention_mask=decoder_attention_mask,
            inputs_embeds=decoder_inputs_embeds,
            past_key_values=past_key_values,
            encoder_hidden_states=hidden_states,
            encoder_attention_mask=attention_mask,
            output_router_logits=output_router_logits,
            **kwargs,
        )

        sequence_output = decoder_outputs.last_hidden_state

        if self.config.tie_word_embeddings:
            # Rescale output before projecting on vocab
            # See https://github.com/tensorflow/mesh/blob/fa19d69eafc9a482aff0b59ddd96b025c0cb207d/mesh_tensorflow/transformer/transformer.py#L586
            sequence_output = sequence_output * (self.model_dim**-0.5)

        lm_logits = self.lm_head(sequence_output)

        loss = None
        encoder_z_loss = None
        encoder_aux_loss = None
        decoder_z_loss = None
        decoder_aux_loss = None

        if output_router_logits:
            # Compute the router loss (z_loss + auxiliary loss) for each router in the encoder and decoder
            if self.encoder.config.encoder_sparse_step > 1:
                encoder_router_logits, encoder_expert_indexes = self._unpack_router_logits(encoder_outputs[-1])
                encoder_z_loss = router_z_loss_func(encoder_router_logits)
                encoder_router_probs = nn.Softmax(dim=-1)(encoder_router_logits)
                encoder_aux_loss = load_balancing_loss_func(encoder_router_probs, encoder_expert_indexes)
            else:
                encoder_z_loss = 0
                encoder_aux_loss = 0

            if self.decoder.config.decoder_sparse_step > 1:
                decoder_router_logits, decoder_expert_indexes = self._unpack_router_logits(decoder_outputs[-1])
                decoder_z_loss = router_z_loss_func(decoder_router_logits)
                decoder_router_probs = nn.Softmax(dim=-1)(decoder_router_logits)
                decoder_aux_loss = load_balancing_loss_func(decoder_router_probs, decoder_expert_indexes)
            else:
                decoder_z_loss = 0
                decoder_aux_loss = 0

        if labels is not None:
            loss_fct = CrossEntropyLoss(ignore_index=-100)
            # move labels to correct device to enable PP
            labels = labels.to(lm_logits.device)
            loss = loss_fct(lm_logits.view(-1, lm_logits.size(-1)), labels.view(-1))

            if output_router_logits:
                z_loss = self.router_z_loss_coef * (encoder_z_loss + decoder_z_loss)
                aux_loss = self.router_aux_loss_coef * (encoder_aux_loss + decoder_aux_loss)
                loss = loss + z_loss + aux_loss

        return Seq2SeqMoEOutput(
            loss=loss,
            logits=lm_logits,
            encoder_z_loss=encoder_z_loss,
            encoder_aux_loss=encoder_aux_loss,
            decoder_z_loss=decoder_z_loss,
            decoder_aux_loss=decoder_aux_loss,
            past_key_values=decoder_outputs.past_key_values,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            decoder_router_logits=decoder_outputs.router_logits,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
            encoder_router_logits=encoder_outputs.router_logits,
        )
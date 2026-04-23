def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutput:
        r"""
        Example:

        ```python
        >>> from transformers import AutoTokenizer, ProphetNetEncoder
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> model = ProphetNetEncoder.from_pretrained("patrickvonplaten/prophetnet-large-uncased-standalone")
        >>> inputs = tokenizer("Hello, my dog is cute", return_tensors="pt")
        >>> outputs = model(**inputs)

        >>> last_hidden_states = outputs.last_hidden_state
        ```"""

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is None and inputs_embeds is None:
            raise ValueError("Either input_ids or inputs_embeds has to be passed.")
        elif input_ids is not None and inputs_embeds is not None:
            raise ValueError("Make sure to only pass input_ids or inputs_embeds.")
        elif input_ids is not None and inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        # prepare attention mask
        if attention_mask is not None:
            extended_attention_mask = (
                1.0 - attention_mask[:, None, None, :].repeat(1, self.config.num_encoder_attention_heads, 1, 1)
            ) * torch.finfo(self.dtype).min
            extended_attention_mask = extended_attention_mask.to(inputs_embeds.dtype)
        else:
            extended_attention_mask = None

        position_embeddings, position_ids = self.position_embeddings(inputs_embeds.shape[:2], inputs_embeds.device)

        hidden_states = inputs_embeds + position_embeddings
        hidden_states = self.embeddings_layer_norm(hidden_states)
        hidden_states = nn.functional.dropout(hidden_states, p=self.config.dropout, training=self.training)

        encoder_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        for idx, encoder_layer in enumerate(self.layers):
            if output_hidden_states:
                encoder_hidden_states = encoder_hidden_states + (hidden_states,)

            layer_outputs = encoder_layer(
                hidden_states,
                attention_mask=extended_attention_mask,
                output_attentions=output_attentions,
            )

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_attentions = all_attentions + (layer_outputs[1],)

        if output_hidden_states:
            encoder_hidden_states = encoder_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, encoder_hidden_states, all_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states, hidden_states=encoder_hidden_states, attentions=all_attentions
        )
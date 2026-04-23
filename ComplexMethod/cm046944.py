def forward(
            self,
            input_ids: Optional[torch.Tensor] = None,
            attention_mask: Optional[torch.Tensor] = None,
            head_mask: Optional[torch.Tensor] = None,
            inputs_embeds: Optional[torch.Tensor] = None,
            output_attentions: Optional[bool] = None,
            output_hidden_states: Optional[bool] = None,
            return_dict: Optional[bool] = None,
        ):
            output_attentions = (
                output_attentions
                if output_attentions is not None
                else self.config.output_attentions
            )
            output_hidden_states = (
                output_hidden_states
                if output_hidden_states is not None
                else self.config.output_hidden_states
            )
            return_dict = (
                return_dict if return_dict is not None else self.config.use_return_dict
            )

            if input_ids is not None and inputs_embeds is not None:
                raise ValueError(
                    "You cannot specify both input_ids and inputs_embeds at the same time"
                )
            elif input_ids is not None:
                self.warn_if_padding_and_no_attention_mask(input_ids, attention_mask)
                input_shape = input_ids.size()
            elif inputs_embeds is not None:
                input_shape = inputs_embeds.size()[:-1]
            else:
                raise ValueError(
                    "You have to specify either input_ids or inputs_embeds"
                )

            device = input_ids.device if input_ids is not None else inputs_embeds.device

            head_mask_is_none = head_mask is None
            # Prepare head mask if needed
            head_mask = self.get_head_mask(head_mask, self.config.num_hidden_layers)

            embeddings = self.embeddings(
                input_ids, inputs_embeds
            )  # (bs, seq_length, dim)

            if self.config._attn_implementation == "flash_attention_2":
                attention_mask = (
                    attention_mask
                    if (attention_mask is not None and 0 in attention_mask)
                    else None
                )
            else:
                if attention_mask is None:
                    attention_mask = torch.ones(
                        input_shape, device = device
                    )  # (bs, seq_length)

                if (
                    self.config._attn_implementation == "sdpa"
                    and head_mask_is_none
                    and not output_attentions
                ):
                    attention_mask = _prepare_4d_attention_mask_for_sdpa(
                        attention_mask, embeddings.dtype, tgt_len = input_shape[1]
                    )
            # patch here, change kwargs to positional args:
            return self.transformer(
                embeddings,
                attention_mask,
                head_mask,
                output_attentions,
                output_hidden_states,
                return_dict,
            )
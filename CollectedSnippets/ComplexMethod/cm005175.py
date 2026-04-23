def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        mems: torch.Tensor | None = None,
        perm_mask: torch.Tensor | None = None,
        target_mapping: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        input_mask: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        start_positions: torch.Tensor | None = None,
        end_positions: torch.Tensor | None = None,
        use_mems: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,  # delete when `use_cache` is removed in XLNetModel
    ) -> tuple | XLNetForQuestionAnsweringSimpleOutput:
        r"""
        mems (`list[torch.FloatTensor]` of length `config.n_layers`):
            Contains pre-computed hidden-states (see `mems` output below) . Can be used to speed up sequential
            decoding. The token ids which have their past given to this model should not be passed as `input_ids` as
            they have already been computed.

            `use_mems` has to be set to `True` to make use of `mems`.
        perm_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length, sequence_length)`, *optional*):
            Mask to indicate the attention pattern for each input token with values selected in `[0, 1]`:

            - if `perm_mask[k, i, j] = 0`, i attend to j in batch k;
            - if `perm_mask[k, i, j] = 1`, i does not attend to j in batch k.

            If not set, each token attends to all the others (full bidirectional attention). Only used during
            pretraining (to define factorization order) or for sequential decoding (generation).
        target_mapping (`torch.FloatTensor` of shape `(batch_size, num_predict, sequence_length)`, *optional*):
            Mask to indicate the output tokens to use. If `target_mapping[k, i, j] = 1`, the i-th predict in batch k is
            on the j-th token. Only used during pretraining for partial prediction or for sequential decoding
            (generation).
        input_mask (`torch.FloatTensor` of shape `batch_size, sequence_length`, *optional*):
            Mask to avoid performing attention on padding token indices. Negative of `attention_mask`, i.e. with 0 for
            real tokens and 1 for padding which is kept for compatibility with the original code base.

            Mask values selected in `[0, 1]`:

            - 1 for tokens that are **masked**,
            - 0 for tokens that are **not masked**.

            You can only uses one of `input_mask` and `attention_mask`.
        use_mems (`bool`, *optional*):
            Whether to use memory states to speed up sequential decoding. If set to `True`, the model will use the hidden
            states from previous forward passes to compute attention, which can significantly improve performance for
            sequential decoding tasks.
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.transformer(
            input_ids,
            attention_mask=attention_mask,
            mems=mems,
            perm_mask=perm_mask,
            target_mapping=target_mapping,
            token_type_ids=token_type_ids,
            input_mask=input_mask,
            inputs_embeds=inputs_embeds,
            use_mems=use_mems,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            **kwargs,
        )

        sequence_output = outputs[0]

        logits = self.qa_outputs(sequence_output)
        start_logits, end_logits = logits.split(1, dim=-1)
        start_logits = start_logits.squeeze(-1).contiguous()
        end_logits = end_logits.squeeze(-1).contiguous()

        total_loss = None
        if start_positions is not None and end_positions is not None:
            # If we are on multi-GPU, split add a dimension
            if len(start_positions.size()) > 1:
                start_positions = start_positions.squeeze(-1)
            if len(end_positions.size()) > 1:
                end_positions = end_positions.squeeze(-1)
            # sometimes the start/end positions are outside our model inputs, we ignore these terms
            ignored_index = start_logits.size(1)
            start_positions = start_positions.clamp(0, ignored_index)
            end_positions = end_positions.clamp(0, ignored_index)

            loss_fct = CrossEntropyLoss(ignore_index=ignored_index)
            start_loss = loss_fct(start_logits, start_positions)
            end_loss = loss_fct(end_logits, end_positions)
            total_loss = (start_loss + end_loss) / 2

        if not return_dict:
            output = (start_logits, end_logits) + outputs[1:]
            return ((total_loss,) + output) if total_loss is not None else output

        return XLNetForQuestionAnsweringSimpleOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            mems=outputs.mems,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )
def MistralForCausalLM_fast_forward(
    self,
    input_ids: torch.LongTensor = None,
    causal_mask: Optional[BlockDiagonalCausalMask] = None,
    attention_mask: Optional[torch.Tensor] = None,
    position_ids: Optional[torch.LongTensor] = None,
    past_key_values: Optional[List[torch.FloatTensor]] = None,
    inputs_embeds: Optional[torch.FloatTensor] = None,
    labels: Optional[torch.LongTensor] = None,
    use_cache: Optional[bool] = None,
    output_attentions: Optional[bool] = None,
    output_hidden_states: Optional[bool] = None,
    return_dict: Optional[bool] = None,
    num_logits_to_keep: Optional[int] = 0,
    logits_to_keep: Optional[int] = 0,
    *args,
    **kwargs,
) -> Union[Tuple, CausalLMOutputWithPast]:
    if causal_mask is None and past_key_values is None:
        bsz, q_len = input_ids.shape
        sliding_window = getattr(self.config, "sliding_window", None)

        if HAS_XFORMERS:
            # Always create causal mask for xformers
            if (
                sliding_window is None
                or sliding_window == "null"
                or sliding_window <= 0
            ):
                causal_mask = xformers.attn_bias.LowerTriangularMask()
            elif q_len <= sliding_window:
                causal_mask = xformers.attn_bias.LowerTriangularMask()
            else:
                causal_mask = xformers.attn_bias.BlockDiagonalCausalMask.from_seqlens(
                    [q_len] * bsz
                ).make_local_attention(window_size = sliding_window)

            # If attention_mask exists, it will be handled in the attention forward

        elif self.training:
            # During training, LlamaModel_fast_forward's DPO embed-masking
            # block requires a 2D attention_mask (it does
            # inputs_embeds *= attention_mask.unsqueeze(0).transpose(0, 1).transpose(1, 2)).
            # Afterwards, LlamaModel_fast_forward sets attention_mask=None
            # before the attention layers anyway, so leaving the 2D mask
            # untouched here is safe and avoids converting to 4D (which would
            # crash the DPO block).
            pass

        else:
            # Not using xformers - need to create attention masks
            if (
                sliding_window is None
                or sliding_window == "null"
                or sliding_window <= 0
                or q_len <= sliding_window
            ):
                # Fully causal mask
                causal_mask_values = torch.triu(
                    torch.full((q_len, q_len), -torch.inf, device = input_ids.device),
                    diagonal = 1,
                )
            else:
                # Sliding window attention
                q_indices = torch.arange(q_len, device = input_ids.device).view(-1, 1)
                k_indices = torch.arange(q_len, device = input_ids.device).view(1, -1)

                causal_bool_mask = k_indices <= q_indices
                window_bool_mask = (q_indices - k_indices) < sliding_window

                causal_mask_values = torch.where(
                    causal_bool_mask & window_bool_mask, 0.0, -torch.inf
                )

            # Combine with existing attention_mask if present
            if attention_mask is None:
                attention_mask = causal_mask_values[None, None, :, :].expand(
                    bsz, 1, q_len, q_len
                )
            else:
                if attention_mask.dim() == 2:
                    # Convert 0/1 padding mask to additive format: 1->0 (keep), 0->-inf (mask)
                    padding_mask = torch.where(
                        attention_mask[:, None, None, :].bool(),
                        0.0,
                        -torch.inf,
                    )
                    attention_mask = causal_mask_values[None, None, :, :] + padding_mask
                else:
                    attention_mask = (
                        attention_mask + causal_mask_values[None, None, :, :]
                    )

            attention_mask = attention_mask.to(
                dtype = _get_dtype(dtype_from_config(self.config))
            )

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

    # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
    self.model._has_no_labels = labels is None

    if past_key_values is not None:
        outputs = LlamaModel_fast_forward_inference(
            self,
            input_ids,
            past_key_values,
            position_ids = position_ids,
            attention_mask = attention_mask,
        )
    else:
        outputs = self.model(
            input_ids = input_ids,
            causal_mask = causal_mask,
            attention_mask = attention_mask,
            position_ids = position_ids,
            past_key_values = past_key_values,
            inputs_embeds = inputs_embeds,
            use_cache = use_cache,
            output_attentions = output_attentions,
            output_hidden_states = output_hidden_states,
            return_dict = return_dict,
            **kwargs,
        )

    hidden_states = outputs[0]

    bsz, q_len, hd = hidden_states.shape
    lm_head = self.lm_head.weight
    lm_head_device = lm_head.device

    # Move items to same device as lm_head
    hidden_states = hidden_states.to(lm_head_device)
    if labels is not None:
        labels = labels.to(lm_head_device)

    # If we are in GRPO mode, return raw hidden states
    if os.environ.get("UNSLOTH_RETURN_HIDDEN_STATES", "0") == "1":
        num_logits_to_keep = max(num_logits_to_keep, logits_to_keep)
        if num_logits_to_keep != 0:
            hidden_states = hidden_states[:, -num_logits_to_keep:, :]
        return CausalLMOutputWithPast(
            loss = None,
            logits = hidden_states,
            past_key_values = outputs.past_key_values,
            hidden_states = outputs.hidden_states,
            attentions = outputs.attentions,
        )

    if bsz == 1 and q_len == 1:
        logits = torch.mv(lm_head, hidden_states.ravel().to(lm_head.dtype))
        logits = logits.unsqueeze(0).unsqueeze(0)
    elif num_logits_to_keep != 0:
        logits = self.lm_head(
            hidden_states[:, -num_logits_to_keep:, :].to(lm_head.dtype)
        )
    else:
        RETURN_LOGITS = os.environ.get("UNSLOTH_RETURN_LOGITS", "0") == "1"
        # < 1024 Normal Unsloth uses less VRAM!
        if bsz * q_len <= 1024 and not RETURN_LOGITS:
            # Use unsloth_fused_ce_loss which actually calculates the best chunk size to reduce VRAM usage
            RETURN_LOGITS = False

        if not RETURN_LOGITS and labels is not None:
            n_items = kwargs.get("num_items_in_batch", None)
            if n_items is None:
                n_items = kwargs.get("n_items", None)
            logit_softcapping = getattr(self.config, "final_logit_softcapping", 0)

            # loss = fused_linear_cross_entropy(
            #     hidden_states = hidden_states,
            #     lm_weight = lm_head,
            #     labels = labels,
            #     num_items_in_batch = n_items,
            #     logit_softcapping = logit_softcapping,
            # )
            loss = unsloth_fused_ce_loss(
                trainer = None,
                hidden_states = hidden_states,
                lm_head_weight = lm_head,
                lm_head_bias = None,
                labels = labels,
                mask = None,
                n_items = n_items,
                scaling = getattr(self, "accelerator_scaler", None),
                target_gb = None,
                torch_compile = True,
                logit_softcapping = logit_softcapping,
            )
            if not return_dict:
                output = (logits,) + outputs[1:]
                return (loss,) + output if loss is not None else output

            output = CausalLMOutputWithPast(
                loss = loss,
                logits = EMPTY_LOGITS,
                past_key_values = outputs.past_key_values,
                hidden_states = outputs.hidden_states,
                attentions = outputs.attentions,
            )
            return output
        pass
        logits = self.lm_head(hidden_states.to(lm_head.dtype))
    logits = logits.to(_get_dtype(dtype_from_config(self.config)))

    loss = None
    if labels is not None:
        shift_logits = logits
        # if not hasattr(self, "extra_ignored_labels"):
        #     # Fixes https://github.com/unslothai/unsloth/issues/10
        #     self.extra_ignored_labels = torch.full((self.max_seq_length, 1), -100, device = "cuda:0")
        # pass
        # shift_labels = torch.hstack((labels[..., 1:], self.extra_ignored_labels[:labels.shape[0]]))
        shift_labels = torch.empty_like(labels)
        shift_labels[..., :-1] = labels[..., 1:]
        shift_labels[..., -1] = -100
        mask_packed_sequence_boundaries(
            shift_labels,
            kwargs.get("packed_seq_lengths"),
        )
        n_items = kwargs.get("num_items_in_batch", None)
        if n_items is None:
            n_items = kwargs.get("n_items", None)
        loss = fast_cross_entropy_loss(
            logits = shift_logits,
            labels = shift_labels,
            n_items = n_items,
        )

    if not return_dict:
        output = (logits,) + outputs[1:]
        return (loss,) + output if loss is not None else output

    return CausalLMOutputWithPast(
        loss = loss,
        logits = logits,
        past_key_values = outputs.past_key_values,
        hidden_states = outputs.hidden_states,
        attentions = outputs.attentions,
    )
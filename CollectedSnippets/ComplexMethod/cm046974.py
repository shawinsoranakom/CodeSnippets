def _CausalLM_fast_forward(
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
        if past_key_values is not None:
            outputs = fast_forward_inference(
                self,
                input_ids,
                past_key_values,
                position_ids = position_ids,
                attention_mask = attention_mask,
                **kwargs,
            )
        else:
            causal_mask = (
                xformers.attn_bias.LowerTriangularMask() if HAS_XFORMERS else None
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

        logit_softcapping = getattr(self.config, "final_logit_softcapping", 0)
        logit_scaling = getattr(self.config, "logit_scale", 0)
        dtype = lm_head.dtype
        num_logits_to_keep = max(num_logits_to_keep, logits_to_keep)

        # Move items to same device as lm_head
        hidden_states = hidden_states.to(lm_head_device)
        if labels is not None:
            labels = labels.to(lm_head_device)

        # Output last hidden states without logits if asked
        if os.environ.get("UNSLOTH_RETURN_HIDDEN_STATES", "0") == "1":
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
            logits = torch.mv(lm_head, hidden_states.ravel().to(dtype))
            logits = logits.unsqueeze(0).unsqueeze(0)
        elif num_logits_to_keep != 0:
            logits = self.lm_head(hidden_states[:, -num_logits_to_keep:, :].to(dtype))
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

                if self.config.model_type == "falcon_h1":
                    hidden_states = hidden_states * self.config.lm_head_multiplier

                ### DISABLED since T4 breaks
                # OutOfResources: out of resource: shared memory, Required: 98304, Hardware limit: 65536. Reducing block sizes or `num_stages` may help.
                # loss = fused_linear_cross_entropy(
                #     hidden_states      = hidden_states,
                #     lm_weight          = lm_head,
                #     labels             = labels,
                #     num_items_in_batch = n_items,
                #     logit_softcapping  = logit_softcapping,
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
            logits = self.lm_head(hidden_states.to(dtype))

        logits = logits.to(_get_dtype(dtype_from_config(self.config)))
        loss = None
        logit_softcapping = getattr(self.config, "final_logit_softcapping", 0)
        logit_scaling = getattr(self.config, "logit_scale", 0)
        if self.config.model_type == "granite":
            # granite uses logit_scaling as key and they divide by the scale unlike cohere
            # notice that for granite, logits_scale is 16 and for cohere it is 0.125 (aka 1/8) in their respective configs
            # granite: https://github.com/huggingface/transformers/blob/4d1d0f29a493098e6bc6b904b82e29cb331827f5/src/transformers/models/granite/modeling_granite.py#L1103
            # cohere: https://github.com/huggingface/transformers/blob/4d1d0f29a493098e6bc6b904b82e29cb331827f5/src/transformers/models/cohere/modeling_cohere.py#L1176
            logit_scaling = 1 / getattr(self.config, "logits_scaling", 1)
        elif self.config.model_type == "falcon_h1":
            logit_scaling = self.config.lm_head_multiplier

        if labels is not None:
            shift_logits = logits
            # if not hasattr(self, "extra_ignored_labels"):
            #     # Fixes https://github.com/unslothai/unsloth/issues/10
            #     self.extra_ignored_labels = torch.full((self.max_seq_length, 1), -100, device = "cuda:0")
            # pass
            shift_labels = torch.empty_like(labels)
            shift_labels[..., :-1] = labels[..., 1:]
            shift_labels[..., -1] = -100
            mask_packed_sequence_boundaries(
                shift_labels,
                kwargs.get("packed_seq_lengths"),
            )
            # shift_labels = torch.hstack((labels[..., 1:], self.extra_ignored_labels[:labels.shape[0]]))
            n_items = kwargs.get("num_items_in_batch", None)
            if n_items is None:
                n_items = kwargs.get("n_items", None)
            loss = fast_cross_entropy_loss(
                logits = shift_logits,
                labels = shift_labels,
                logit_softcapping = logit_softcapping,
                logit_scaling = logit_scaling,
                n_items = n_items,
            )
        else:
            if logit_scaling != 0:
                if logits.requires_grad:
                    logits = logit_scaling * logits
                else:
                    logits *= logit_scaling
            if logit_softcapping != 0:
                if logits.requires_grad:
                    logits = (1.0 / logit_softcapping) * logits
                    logits = torch.tanh(logits)
                    logits = logit_softcapping * logits
                else:
                    logits *= 1.0 / logit_softcapping
                    logits.tanh_()
                    logits *= logit_softcapping

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
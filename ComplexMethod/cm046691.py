def _fixed_csm_forward(
            self,
            input_ids = None,
            input_values = None,
            attention_mask = None,
            input_values_cutoffs = None,
            position_ids = None,
            past_key_values = None,
            inputs_embeds = None,
            labels = None,
            use_cache = None,
            cache_position = None,
            logits_to_keep = 0,
            **kwargs,
        ):
            # Strip non-standard kwargs injected by Unsloth/PEFT (causal_mask,
            # num_logits_to_keep, task_ids, return_dict, etc.)
            output_attentions = kwargs.pop("output_attentions", None)
            output_hidden_states = kwargs.pop("output_hidden_states", None)
            kwargs.pop("return_dict", None)
            kwargs.pop("causal_mask", None)
            kwargs.pop("num_logits_to_keep", None)
            kwargs.pop("task_ids", None)

            # Only keep recognized TransformersKwargs
            clean_kwargs = {
                k: v for k, v in kwargs.items() if k in _TRANSFORMERS_KWARGS
            }

            if input_ids is not None and input_ids.ndim == 2:
                merged = self._merge_input_ids_with_input_values(
                    input_ids, input_values, input_values_cutoffs, labels
                )
                inputs_embeds = merged["inputs_embeds"]
                labels = merged["labels"]
                input_ids = None

            backbone_outputs = self.backbone_model(
                input_ids = input_ids,
                attention_mask = attention_mask,
                position_ids = position_ids,
                past_key_values = past_key_values,
                inputs_embeds = inputs_embeds,
                use_cache = use_cache,
                cache_position = cache_position,
                output_attentions = output_attentions,
                output_hidden_states = output_hidden_states,
                **clean_kwargs,
            )

            backbone_hidden_states = backbone_outputs[0]
            slice_indices = (
                slice(-logits_to_keep, None)
                if isinstance(logits_to_keep, int)
                else logits_to_keep
            )
            backbone_logits = self.lm_head(backbone_hidden_states[:, slice_indices, :])

            loss = None
            backbone_loss = None
            depth_decoder_loss = None
            depth_decoder_outputs = None
            if labels is not None:
                backbone_labels = labels[:, :, 0]
                backbone_loss = self.loss_function(
                    logits = backbone_logits,
                    labels = backbone_labels,
                    vocab_size = self.config.vocab_size,
                    **clean_kwargs,
                )

                train_mask = ~(labels[:, :, 1:] == -100).all(dim = -1)
                depth_decoder_input_ids = labels[train_mask][
                    ..., : self.config.num_codebooks - 1
                ]
                depth_decoder_input_ids = nn.functional.pad(
                    depth_decoder_input_ids, (1, 0), value = 0
                )

                train_idxs = train_mask.nonzero(as_tuple = True)
                backbone_last_hidden_states = backbone_hidden_states[
                    train_idxs[0], train_idxs[1] - 1, :
                ]
                depth_decoder_labels = labels[train_mask]

                # Build clean kwargs for depth decoder
                dd_kwargs = clean_kwargs.copy()
                # Scale num_items_in_batch for depth decoder (31 codebooks)
                if "num_items_in_batch" in dd_kwargs:
                    dd_kwargs["num_items_in_batch"] = dd_kwargs[
                        "num_items_in_batch"
                    ] * (self.config.num_codebooks - 1)

                depth_decoder_outputs = self.depth_decoder(
                    input_ids = depth_decoder_input_ids,
                    backbone_last_hidden_state = backbone_last_hidden_states,
                    use_cache = False,
                    return_dict = True,
                    labels = depth_decoder_labels,
                    output_attentions = output_attentions,
                    output_hidden_states = output_hidden_states,
                    **dd_kwargs,
                )

                depth_decoder_loss = depth_decoder_outputs.loss
                if depth_decoder_loss is None:
                    logger.warning(
                        "CSM depth_decoder_loss is None! "
                        f"labels shape={depth_decoder_labels.shape}, "
                        f"train_mask sum={train_mask.sum().item()}"
                    )
                    # Fallback: use only backbone loss instead of crashing
                    loss = backbone_loss
                else:
                    loss = backbone_loss + depth_decoder_loss

            return CsmOutputWithPast(
                loss = loss,
                backbone_loss = backbone_loss,
                depth_decoder_loss = depth_decoder_loss,
                logits = backbone_logits,
                past_key_values = backbone_outputs.past_key_values,
                hidden_states = backbone_outputs.hidden_states,
                attentions = backbone_outputs.attentions,
                depth_decoder_logits = (
                    depth_decoder_outputs.logits if depth_decoder_outputs else None
                ),
                depth_decoder_past_key_values = (
                    depth_decoder_outputs.past_key_values
                    if depth_decoder_outputs
                    else None
                ),
                depth_decoder_hidden_states = (
                    depth_decoder_outputs.hidden_states
                    if depth_decoder_outputs
                    else None
                ),
                depth_decoder_attentions = (
                    depth_decoder_outputs.attentions if depth_decoder_outputs else None
                ),
            )
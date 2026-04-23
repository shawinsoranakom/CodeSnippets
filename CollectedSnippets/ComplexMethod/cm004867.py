def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        input_values: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        input_values_cutoffs: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | CsmOutputWithPast:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length, num_codebooks) or (batch_size, sequence_length)`):
            1. (batch_size, sequence_length): corresponds to the input sequence prepared with the processor from the text prompt. Such input
            requires `input_values` to be provided so that audio can be encoded in codebook tokens and then merged with the text tokens.

            2. (batch_size, sequence_length, num_codebooks): codebook tokens generated during the autoregressive decoding. Such input is not meant to be used by end users.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        input_values_cutoffs (`torch.Tensor` of shape `(batch_size, max_num_audio)`, *optional*):
            Specify the end positions of audio segments within each batch entry, relative to the concatenated audio input.
            If a batch entry has fewer segments than the maximum, it is padded with -1. For example, in a batch of 2 sequences
            where the first contains 2 audio segments of length l1, and the second contains 1 audio segment of length l2,
            the input_values_cutoffs would be: [[l1, 2 * l1], [l2, -1]].
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should be in `[config.audio_token_id, -100, -101]`.
            Requires targeted `input_values` to be provided as audio tokens will be inferred from it using the `codec_model`.
            - `config.audio_token_id` indicates an audio frames (considering sequence length elements as frames)
            - `-100` will be ignored in the loss computation
            - `-101` indicates the audio frame will be used only for the backbone model (using the first codebook token as labels)

            Such labels can be prepared using `output_labels=True` when calling [`CsmProcessor`].
        logits_to_keep (`int` or `torch.Tensor`, *optional*):
            Kept for compatibility. Does not support another value than:
            1. `0`, which is equivalent to keeping all logits, used in the training regime
            2. `1`, which is equivalent to keeping only the last logit, used in the generation regime

        Example:

        ```python
        >>> import torch
        >>> from transformers import CsmForConditionalGeneration, AutoProcessor
        >>> from datasets import load_dataset, Audio

        >>> model_id = "sesame/csm-1b"
        >>> torch_device = "cuda" if torch.cuda.is_available() else "cpu"

        >>> processor = AutoProcessor.from_pretrained(model_id)

        >>> ds = load_dataset("hf-internal-testing/dailytalk-dummy", split="train")
        >>> # ensure the audio is 24kHz
        >>> ds = ds.cast_column("audio", Audio(sampling_rate=24000))

        >>> conversation = []
        >>> # prepare a conversation with text and corresponding audio
        >>> for text, audio, speaker_id in zip(ds[:4]["text"], ds[:4]["audio"], ds[:4]["speaker_id"]):
        ...     conversation.append(
        ...         {
        ...             "role": f"{speaker_id}",
        ...             "content": [{"type": "text", "text": text}, {"type": "audio", "path": audio["array"]}],
        ...         }
        ...     )

        >>> inputs = processor.apply_chat_template(
        ...     conversation,
        ...     tokenize=True,
        ...     return_dict=True,
        ...     output_labels=True,
        ... ).to(torch_device)

        >>> model = CsmForConditionalGeneration.from_pretrained(model_id, device_map=torch_device)
        >>> output = model(**inputs)
        >>> output.loss.backward()
        ```"""
        if input_ids is not None and input_ids.ndim == 2:
            merged_inputs = self._merge_input_ids_with_input_values(
                input_ids, input_values, input_values_cutoffs, labels
            )
            inputs_embeds = merged_inputs["inputs_embeds"]
            labels = merged_inputs["labels"]
            input_ids = None

        backbone_outputs = self.backbone_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            **kwargs,
        )

        backbone_hidden_states = backbone_outputs[0]
        # Only compute necessary logits, and do not upcast them to float if we are not computing the loss
        slice_indices = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
        backbone_logits = self.lm_head(backbone_hidden_states[:, slice_indices, :])

        loss = None
        backbone_loss = None
        depth_decoder_loss = None
        depth_decoder_outputs = None
        if labels is not None:
            # select first codebook as labels for the backbone model
            backbone_labels = labels[:, :, 0]
            backbone_loss = self.loss_function(
                logits=backbone_logits, labels=backbone_labels, vocab_size=self.config.vocab_size, **kwargs
            )

            # for the depth decoder, we need to select the frames to train on
            # those are frames where the label is not uniformly `ignore_index` along the codebook dimension
            train_mask = ~(labels[:, :, 1:] == -100).all(dim=-1)
            depth_decoder_input_ids = labels[train_mask][..., : self.config.num_codebooks - 1]
            # add place holder in position 0 that will be replaced by the backbone_last_hidden_state
            depth_decoder_input_ids = nn.functional.pad(depth_decoder_input_ids, (1, 0), value=0)

            train_idxs = train_mask.nonzero(as_tuple=True)
            backbone_last_hidden_states = backbone_hidden_states[train_idxs[0], train_idxs[1] - 1, :]
            depth_decoder_labels = labels[train_mask]

            depth_decoder_outputs = self.depth_decoder(
                input_ids=depth_decoder_input_ids,
                backbone_last_hidden_state=backbone_last_hidden_states,
                use_cache=use_cache,
                return_dict=True,
                labels=depth_decoder_labels,
                **kwargs,
            )

            depth_decoder_loss = depth_decoder_outputs.loss
            loss = backbone_loss + depth_decoder_loss

        return CsmOutputWithPast(
            loss=loss,
            backbone_loss=backbone_loss,
            depth_decoder_loss=depth_decoder_loss,
            logits=backbone_logits,
            past_key_values=backbone_outputs.past_key_values,
            hidden_states=backbone_outputs.hidden_states,
            attentions=backbone_outputs.attentions,
            depth_decoder_logits=depth_decoder_outputs.logits if depth_decoder_outputs is not None else None,
            depth_decoder_past_key_values=depth_decoder_outputs.past_key_values
            if depth_decoder_outputs is not None
            else None,
            depth_decoder_hidden_states=depth_decoder_outputs.hidden_states
            if depth_decoder_outputs is not None
            else None,
            depth_decoder_attentions=depth_decoder_outputs.attentions if depth_decoder_outputs is not None else None,
        )
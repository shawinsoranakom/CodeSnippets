def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        thinker_reply_part: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        rope_deltas: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        input_text_ids: torch.LongTensor | None = None,
        image_grid_thw: torch.LongTensor | None = None,
        video_grid_thw: torch.LongTensor | None = None,
        use_audio_in_video: bool | None = None,
        audio_feature_lengths: torch.LongTensor | None = None,
        video_second_per_grid: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple | Qwen2_5OmniTalkerCausalLMOutputWithPast:
        r"""
        thinker_reply_part (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Hidden states from the thinker model's output that represent the text reply part to be processed.
        rope_deltas (`torch.LongTensor` of shape `(batch_size, )`, *optional*):
            The rope index difference between sequence length and multimodal rope.
        input_text_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Input token IDs for text-only content, used for position calculation in multimodal contexts.
        image_grid_thw (`torch.LongTensor` of shape `(num_images, 3)`, *optional*):
            The temporal, height and width of feature shape of each image in LLM.
        video_grid_thw (`torch.LongTensor` of shape `(num_videos, 3)`, *optional*):
            The temporal, height and width of feature shape of each video in LLM.
        use_audio_in_video (`bool`, *optional*):
            Whether or not use audio track in video, should same as the parameter in `process_audio_info`.
        audio_feature_lengths (`torch.LongTensor` of shape `(num_audios)`, *optional*):
            The length of feature shape of each audio in LLM.
        video_second_per_grid (`torch.LongTensor` of shape `(num_videos)`, *optional*):
            Number of seconds per grid for each video, used for temporal feature mapping.

        Example:

        ```python
        >>> from io import BytesIO
        >>> from urllib.request import urlopen
        >>> import librosa
        >>> from transformers import AutoProcessor, Qwen2_5OmniTalkerForConditionalGeneration

        >>> model = Qwen2_5OmniTalkerForConditionalGeneration.from_pretrained("Qwen/Qwen2-Audio-7B")
        >>> processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B")

        >>> prompt = "<|audio_bos|><|AUDIO|><|audio_eos|>Generate the caption in English:"
        >>> url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen2-Audio/audio/glass-breaking-151256.mp3"
        >>> audio, _ = librosa.load(BytesIO(urlopen(url).read()), sr=self.processor.feature_extractor.sampling_rate)

        >>> inputs = processor(text=prompt, audio=audio, return_tensors="pt")

        >>> # Generate
        >>> generate_ids = model.generate(**inputs, max_length=30)
        >>> processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        "Generate the caption in English: Glass is breaking."
        ```"""

        if attention_mask is not None and position_ids is None:
            past_key_values_length = 0 if past_key_values is None else past_key_values.get_seq_length()
            if past_key_values_length == 0 or self.rope_deltas is None:
                position_ids, rope_deltas = self.get_rope_index(
                    input_text_ids,
                    image_grid_thw,
                    video_grid_thw,
                    attention_mask,
                    use_audio_in_video,
                    audio_feature_lengths,
                    video_second_per_grid,
                )

                if inputs_embeds is not None:
                    inputs_embeds[:, -1, :] += self.get_input_embeddings()(
                        torch.tensor([self.codec_bos_token], dtype=torch.long, device=inputs_embeds.device)
                    )
                    inputs_embeds[:, -2, :] += self.get_input_embeddings()(
                        torch.tensor([self.codec_pad_token], dtype=torch.long, device=inputs_embeds.device)
                    )
                self.rope_deltas = rope_deltas

            else:
                if inputs_embeds is not None:
                    batch_size, seq_length, _ = inputs_embeds.shape
                else:
                    batch_size, seq_length = input_ids.shape

                delta = (past_key_values_length + self.rope_deltas).to(input_ids.device)
                position_ids = torch.arange(seq_length, device=input_ids.device)
                position_ids = position_ids.view(1, -1).expand(batch_size, -1)
                position_ids = position_ids.add(delta)
                position_ids = position_ids.unsqueeze(0).expand(3, -1, -1)

        if inputs_embeds is None:
            # 1. Inference tokens after second token
            codec_embeds = self.get_input_embeddings()(input_ids)
            inputs_embeds = codec_embeds + thinker_reply_part[:, :1, :]
            if thinker_reply_part.shape[1] > 1:
                thinker_reply_part = thinker_reply_part[:, 1:, :]

        talker_lm_input = self.thinker_to_talker_proj(inputs_embeds)

        if attention_mask is not None:
            attention_mask = attention_mask.to(inputs_embeds.device)

        outputs = self.model(
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=talker_lm_input,
            use_cache=use_cache,
            return_dict=True,
            **kwargs,
        )

        hidden_states = outputs[0]
        logits = self.codec_head(hidden_states)
        logits = logits.float()

        loss = None

        return Qwen2_5OmniTalkerCausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            rope_deltas=self.rope_deltas,
            thinker_reply_part=thinker_reply_part,
        )
def generate(
        self,
        input_features: torch.Tensor | None = None,
        generation_config: GenerationConfig | None = None,
        logits_processor: LogitsProcessorList | None = None,
        stopping_criteria: StoppingCriteriaList | None = None,
        prefix_allowed_tokens_fn: Callable[[int, torch.Tensor], list[int]] | None = None,
        synced_gpus: bool = False,
        return_timestamps: bool | None = None,
        task: str | None = None,
        language: str | list[str] | None = None,
        is_multilingual: bool | None = None,
        prompt_ids: torch.Tensor | None = None,
        prompt_condition_type: str | None = None,  # first-segment, all-segments
        condition_on_prev_tokens: bool | None = None,
        temperature: float | tuple[float, ...] | None = None,
        compression_ratio_threshold: float | None = None,
        logprob_threshold: float | None = None,
        no_speech_threshold: float | None = None,
        num_segment_frames: int | None = None,
        attention_mask: torch.Tensor | None = None,
        time_precision: float = 0.02,
        time_precision_features: float = 0.01,
        return_token_timestamps: bool | None = None,
        return_segments: bool = False,
        return_dict_in_generate: bool | None = None,
        force_unique_generate_call: bool | None = None,
        monitor_progress: Callable[[torch.Tensor], None] | None = None,
        **kwargs,
    ):
        """
        Transcribes or translates log-mel input features to a sequence of auto-regressively generated token ids.

        <Tip warning={true}>

        Most generation-controlling parameters are set in `generation_config` which, if not passed, will be set to the
        model's default generation configuration. You can override any `generation_config` by passing the corresponding
        parameters to generate(), e.g. `.generate(inputs, num_beams=4, do_sample=True)`.

        For an overview of generation strategies and code examples, check out the [following
        guide](../generation_strategies).

        </Tip>

        Parameters:
            input_features (`torch.Tensor` of shape `(batch_size, feature_size, sequence_length)`, *optional*):
                Float values of log-mel features extracted from the raw speech waveform. The raw speech waveform can be obtained by
                loading a `.flac` or `.wav` audio file into an array of type `list[float]`, a `numpy.ndarray` or a `torch.Tensor`,
                *e.g.*  via the torchcodec library (`pip install torchcodec`) or the soundfile library (`pip install soundfile`).
                To prepare the array into `input_features`, the [`AutoFeatureExtractor`] should be used for extracting the mel
                features, padding and conversion into a tensor of type `torch.FloatTensor`.
                See [`~WhisperFeatureExtractor.__call__`] for details.
            generation_config ([`~generation.GenerationConfig`], *optional*):
                The generation configuration to be used as base parametrization for the generation call. `**kwargs`
                passed to generate matching the attributes of `generation_config` will override them. If
                `generation_config` is not provided, the default will be used, which had the following loading
                priority: 1) from the `generation_config.json` model file, if it exists; 2) from the model
                configuration. Please note that unspecified parameters will inherit [`~generation.GenerationConfig`]'s
                default values, whose documentation should be checked to parameterize generation.
            logits_processor (`LogitsProcessorList`, *optional*):
                Custom logits processors that complement the default logits processors built from arguments and
                generation config. If a logit processor is passed that is already created with the arguments or a
                generation config an error is thrown. This feature is intended for advanced users.
            stopping_criteria (`StoppingCriteriaList`, *optional*):
                Custom stopping criteria that complement the default stopping criteria built from arguments and a
                generation config. If a stopping criteria is passed that is already created with the arguments or a
                generation config an error is thrown. This feature is intended for advanced users.
            prefix_allowed_tokens_fn (`Callable[[int, torch.Tensor], list[int]]`, *optional*):
                If provided, this function constraints the beam search to allowed tokens only at each step. If not
                provided no constraint is applied. This function takes 2 arguments: the batch ID `batch_id` and
                `input_ids`. It has to return a list with the allowed tokens for the next generation step conditioned
                on the batch ID `batch_id` and the previously generated tokens `inputs_ids`. This argument is useful
                for constrained generation conditioned on the prefix, as described in [Autoregressive Entity
                Retrieval](https://huggingface.co/papers/2010.00904).
            synced_gpus (`bool`, *optional*, defaults to `False`):
                Whether to continue running the while loop until max_length (needed to avoid deadlocking with
                `FullyShardedDataParallel` and DeepSpeed ZeRO Stage 3).
            return_timestamps (`bool`, *optional*):
                Whether to return the timestamps with the text. This enables the `WhisperTimestampsLogitsProcessor`.
                For audios longer than 30 seconds, it is necessary to set `return_timestamps=True`.
            task (`str`, *optional*):
                Task to use for generation, either "translate" or "transcribe".
            language (`str` or list of `str`, *optional*):
                Language token to use for generation, can be either in the form of `<|en|>`, `en` or `english`. For
                batched generation, a list of language tokens can be passed. You can find all the possible language
                tokens in the `model.generation_config.lang_to_id` dictionary.
            is_multilingual (`bool`, *optional*):
                Whether or not the model is multilingual.
            prompt_ids (`torch.Tensor`, *optional*):
                Rank-1 tensor of token IDs created by passing text to [`~WhisperProcessor.get_prompt_ids`] that is
                provided as a prompt to each chunk. This can be used to provide or "prompt-engineer" a context for
                transcription, e.g. custom vocabularies or proper nouns to make it more likely to predict those words
                correctly. It cannot be used in conjunction with `decoder_start_token_id` as it overwrites this value.
            prompt_condition_type (`str`, *optional*):
                Only relevant for long-form transcription. Condition type of `prompt_ids`. 'first-segment' means only the first segment is conditioned on `prompt_ids`. 'all-segments' means each segment is conditioned on `prompt_ids`. Make sure to enable `condition_on_prev_tokens` for 'all-segments'.
                Defaults to 'first-segment'. For short-term transcription only 'first-segment' is possible.
            condition_on_prev_tokens (`bool`, *optional*):
                Only relevant for long-form transcription. Whether to condition each segment on the previous segment.
                As shown in the [the Whisper paper](https://cdn.openai.com/papers/whisper.pdf), this can help to improve
                performance.
            temperature (`float` or list of `float`, *optional*):
                The temperature to be used for generation. Passing a single `float` value and `do_sample=True` activates
                generation using sampling. For long-form transcription, temperature fallback can be activated by passing
                a list of float values such as (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). As shown in the [the Whisper paper](https://cdn.openai.com/papers/whisper.pdf), this can help to improve
                performance.
            compression_ratio_threshold (`float`, *optional*):
                Only relevant for long-form transcription. If defined, the zlib compression rate of each segment will be computed. If the compression rate of
                a segment is higher than `compression_ratio_threshold`, temperature fallback is activated: the generated segment is discarded and the generation is
                repeated using a higher temperature. The intuition behind this feature is that segments with very high compression rates
                suffer from a lot of repetition. The unwanted repetition can be reduced by injecting more randomness by increasing the temperature. If `compression_ratio_threshold` is defined
                make sure that `temperature` is a list of values. A common value for `compression_ratio_threshold` is 1.35.
                As shown in the [the Whisper paper](https://cdn.openai.com/papers/whisper.pdf), this can help to improve
                performance.
            logprob_threshold (`float`, *optional*):
                Only relevant for long-form transcription. If defined, the average log-probability of each segment will be computed. If the log-probability of
                a given segment is lower than `logprob_threshold`, temperature fallback is activated: the generated segment is discarded and the generation is
                repeated using a higher temperature. The intuition behind this feature is that segments of low log-probability
                can be improved by injecting more randomness by increasing the temperature. If `logprob_threshold` is defined
                make sure that `temperature` is a list of values. A common value for `logprob_threshold` is -1.0.
                As shown in the [the Whisper paper](https://cdn.openai.com/papers/whisper.pdf), this can help to improve
                performance.
            no_speech_threshold (`float`, *optional*):
                Only relevant for long-form transcription. If defined, the "no-speech" token combined with the `logprob_threshold`
                is used to determine whether a segment contains only silence. In this case, the transcription for this segment
                is skipped.
                As shown in the [the Whisper paper](https://cdn.openai.com/papers/whisper.pdf), this can help to improve
                performance.
            num_segment_frames (`int`, *optional*):
                The number of frames a single segment is made of. If not defined, `num_segment_frames` defaults to the model's stride
                times the maximum input length.
            attention_mask (`torch.Tensor`, *optional*):
                `attention_mask` needs to be passed when doing long-form transcription using a batch size > 1.
            time_precision (`int`, *optional*, defaults to 0.02):
                The duration of output token in seconds. *E.g.* 0.02 means that a generated token on average accounts
                for 20 ms.
            time_precision_features (`int`, *optional*, defaults to 0.01):
                The duration represented by a feature frame in seconds.
            return_token_timestamps (`bool`, *optional*):
                Whether to return token-level timestamps with the text. This can be used with or without the
                `return_timestamps` option. To get word-level timestamps, use the tokenizer to group the tokens into
                words.
            return_segments (`bool`, *optional*, defaults to `False`):
                Whether to additionally return a list of all segments. Note that this option can only be enabled
                when doing long-form transcription.
            return_dict_in_generate (`bool`, *optional*, defaults to `False`):
                Whether or not to return a [`~utils.ModelOutput`] instead of just returning the generated tokens.
                Note that when doing long-form transcription, `return_dict_in_generate` can only be enabled when
                `return_segments` is set True. In this case the generation outputs of each segment is added to each
                segment.
            force_unique_generate_call (`bool`, *optional*):
                Whether to force a unique call to the underlying GenerationMixin's [`~generation.GenerationMixin.generate`] method. This is useful for assisted decoding and testing purposes to ensure
                that only one call to [`~generation.GenerationMixin.generate`] is made and therefore decoder input token ids and eos token ids are returned.
            monitor_progress (`Callable[[torch.Tensor], None]`, *optional*):
                If provided, this function can be called to report the progress of the audio transcription. The function
                takes a tensor argument `p` of shape `(n, 2)`, where `n` is the batch size. `p[i, 0]`  contains the
                index of the audio frame that is currently being transcribed for batch item `i`. `p[i, 1]` contains
                the total number of frames for batch item `i`. No return value is expected.
            kwargs (`dict[str, Any]`, *optional*):
                Ad hoc parametrization of `generate_config` and/or additional model-specific kwargs that will be
                forwarded to the `forward` function of the model. If the model is an encoder-decoder model, encoder
                specific kwargs should not be prefixed and decoder specific kwargs should be prefixed with *decoder_*.
        Return:
            [`~utils.ModelOutput`] or `dict[str, Any]` or `torch.LongTensor`:

                One of the following:
                - [`~utils.ModelOutput`] when `return_dict_in_generate=True` and (`return_timestamps=False` or `force_unique_generate_call=True`), including the decoder input ids and end of sequence id.
                - `dict[str, Any]` when (`return_dict_in_generate=True` and `return_timestamps=True`) or `return_segments=True` or `return_token_timestamps=True`.
                - `torch.LongTensor` in all other cases, excluding the decoder input ids and end of sequence id.

                The possible [`~utils.ModelOutput`] types are:
                - [`~generation.GenerateEncoderDecoderOutput`]
                - [`~generation.GenerateBeamEncoderDecoderOutput`]

                `segments` is a list of lists (one list per batch element) of `segment`.
                A `segment` is a dictionary with keys `start`, `end`, `tokens`, `idxs`, and `result`.
                - `start`: the start timestamp of the segment.
                - `end`: the end timestamp of the segment.
                - `tokens`: the tokens of the segment, excluding the decoder input ids and end of sequence id.
                - `idxs`: the start (included) and end (excluded) indices of the `tokens` of the segment in the underlying call to GenerationMixin's [`~generation.GenerationMixin.generate`] (present in `result`).
                - `result`: the result of the underlying call to GenerationMixin's [`~generation.GenerationMixin.generate`].

                When `return_timestamps=True`, `return_dict_in_generate=True` applies to each call of the underlying GenerationMixin's [`~generation.GenerationMixin.generate`], with outputs stored in `result` of each `segment`.

        Example:

        - *Longform transcription*: To transcribe or translate audios longer than 30 seconds, process the audio files without truncation and pass all mel features at once to generate. It is necessary to set `return_timestamps=True`.
        Indeed, long-form transcription uses a sequential algorithm based on timestamps predictions, with heuristics like compression ratio threshold, log probability threshold and temperature fallback. This algorithm is described in the [the Whisper original paper](https://cdn.openai.com/papers/whisper.pdf), section *3.8. Long-form Transcription*.

        ```python
        >>> import torch
        >>> from transformers import AutoProcessor, WhisperForConditionalGeneration
        >>> from datasets import load_dataset, Audio

        >>> processor = AutoProcessor.from_pretrained("openai/whisper-tiny.en")
        >>> model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en")
        >>> model.cuda()  # doctest: +IGNORE_RESULT

        >>> # load audios > 30 seconds
        >>> ds = load_dataset("distil-whisper/meanwhile", "default")["test"]
        >>> # resample to 16kHz
        >>> ds = ds.cast_column("audio", Audio(sampling_rate=16000))
        >>> # take first 8 audios and retrieve array
        >>> audio = ds[:8]["audio"]
        >>> audio = [x["array"] for x in audio]

        >>> # make sure to NOT truncate the input audio, to return the `attention_mask` and to pad to the longest audio
        >>> inputs = processor(audio, return_tensors="pt", truncation=False, padding="longest", return_attention_mask=True, sampling_rate=16_000)
        >>> inputs = inputs.to("cuda", torch.float32)

        >>> # transcribe audio to ids
        >>> generated_ids = model.generate(**inputs, return_timestamps=True)

        >>> transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)
        >>> transcription[0]
        " Folks, if you watch the show, you know, I spent a lot of time right over there. Patiently and astutely scrutinizing the boxwood and mahogany chest set of the day's biggest stories developing the central headline pawns, definitely maneuvering an oso topical night to F6, fainting a classic Sicilian, nade door variation on the news, all the while seeing eight moves deep and patiently marshalling the latest press releases into a fisher's shows in Lip Nitsky attack that culminates in the elegant lethal slow-played, all-passant checkmate that is my nightly monologue. But sometimes, sometimes, folks, I. CHEERING AND APPLAUSE Sometimes I startle away, cubside down in the monkey bars of a condemned playground on a super fun site. Get all hept up on goofballs. Rummage that were discarded tag bag of defective toys. Yank out a fist bowl of disembodied doll limbs, toss them on a stained kid's place mat from a defunct dennies. set up a table inside a rusty cargo container down by the Wharf and challenged toothless drifters to the godless bughouse blitz of tournament that is my segment. Meanwhile."
        ```

        The `monitor_progress` callback can be used to monitor the progress of the transcription:
        ```python
        >>> from tqdm import tqdm

        >>> # prepare inputs like above

        >>> # define a callback to monitor the progress of the transcription.
        >>> with tqdm(desc="Progress") as pbar:
        >>>     def monitor_progress(p_batch):
        >>>         i = torch.argmax(p_batch[:, 1])
        >>>         p = p_batch[i].detach().cpu()
        >>>         pbar.total = int(p[1])
        >>>         pbar.n = int(p[0])
        >>>         pbar.update()

        >>>     # transcribe audio to ids
        >>>     generated_ids = model.generate(**inputs, return_timestamps=True, monitor_progress=monitor_progress)

        >>> transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)
        >>> transcription[0]
        Progress:  95%|█████████████████████████████████████████████████████████████████████████████████████████████████▎    | 8497/8901 [00:04<00:00, 2052.79it/s]
        " Folks, if you watch the show, you know, I spent a lot of time right over there. Patiently and astutely scrutinizing the boxwood and mahogany chest set of the day's biggest stories developing the central headline pawns, definitely maneuvering an oso topical night to F6, fainting a classic Sicilian, nade door variation on the news, all the while seeing eight moves deep and patiently marshalling the latest press releases into a fisher's shows in Lip Nitsky attack that culminates in the elegant lethal slow-played, all-passant checkmate that is my nightly monologue. But sometimes, sometimes, folks, I. CHEERING AND APPLAUSE Sometimes I startle away, cubside down in the monkey bars of a condemned playground on a super fun site. Get all hept up on goofballs. Rummage that were discarded tag bag of defective toys. Yank out a fist bowl of disembodied doll limbs, toss them on a stained kid's place mat from a defunct dennies. set up a table inside a rusty cargo container down by the Wharf and challenged toothless drifters to the godless bughouse blitz of tournament that is my segment. Meanwhile."
        ```

        - *Shortform transcription*: If passed mel input features are <= 30 seconds, there are two possibilities:
            - `return_timestamps=False`: the whole audio will be transcribed with a single call to GenerationMixin's [`~generation.GenerationMixin.generate`].
            - `return_timestamps=True`: the audio will be transcribed using the same logic as long-form transcription.

        ```python
        >>> import torch
        >>> from transformers import AutoProcessor, WhisperForConditionalGeneration
        >>> from datasets import load_dataset

        >>> processor = AutoProcessor.from_pretrained("openai/whisper-tiny.en")
        >>> model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en")

        >>> ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")

        >>> inputs = processor(ds[0]["audio"]["array"], return_tensors="pt")
        >>> input_features = inputs.input_features

        >>> generated_ids = model.generate(inputs=input_features)

        >>> transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        >>> transcription
        ' Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.'
        ```

        """
        # 1. prepare generation config
        generation_config, kwargs = self._prepare_generation_config(generation_config, **kwargs)

        # 2. set global generate variables
        input_stride = self.model.encoder.conv1.stride[0] * self.model.encoder.conv2.stride[0]
        num_segment_frames = input_stride * self.config.max_source_positions
        batch_size, total_input_frames = self._retrieve_total_input_frames(
            input_features=input_features, input_stride=input_stride, kwargs=kwargs
        )
        is_shortform = total_input_frames <= num_segment_frames

        # 3. Make sure generation config is correctly set
        # Make sure the generation config is correctly set depending on whether timestamps are to be returned or not
        return_dict_in_generate = self._set_return_outputs(
            return_dict_in_generate=return_dict_in_generate,
            return_token_timestamps=return_token_timestamps,
            logprob_threshold=logprob_threshold,
            generation_config=generation_config,
        )
        timestamp_begin = self._set_return_timestamps(
            return_timestamps=return_timestamps, is_shortform=is_shortform, generation_config=generation_config
        )
        self._set_language_and_task(
            language=language, task=task, is_multilingual=is_multilingual, generation_config=generation_config
        )
        self._set_num_frames(
            return_token_timestamps=return_token_timestamps,
            generation_config=generation_config,
            attention_mask=attention_mask,
            kwargs=kwargs,
        )
        self._set_thresholds_and_condition(
            generation_config=generation_config,
            logprob_threshold=logprob_threshold,
            compression_ratio_threshold=compression_ratio_threshold,
            no_speech_threshold=no_speech_threshold,
            condition_on_prev_tokens=condition_on_prev_tokens,
        )
        self._set_prompt_condition_type(
            generation_config=generation_config,
            prompt_condition_type=prompt_condition_type,
        )

        # pass self.config for backward compatibility
        init_tokens = self._retrieve_init_tokens(
            input_features,
            batch_size=batch_size,
            generation_config=generation_config,
            config=self.config,
            num_segment_frames=num_segment_frames,
            kwargs=kwargs,
        )
        # passing `decoder_input_ids` is deprecated - the only exception is for assisted generation
        # where the input ids are handled explicitly by the generate method
        self._check_decoder_input_ids(kwargs=kwargs)
        # `output_attentions` is deprecated - we force eager attention if this feature is
        # indirectly requested, e.g. through return_token_timestamps
        if return_token_timestamps:
            self.model.config._attn_implementation = "eager"

        # 3. Retrieve logits processors
        device = kwargs["encoder_outputs"][0].device if "encoder_outputs" in kwargs else input_features.device
        begin_index = init_tokens.shape[1]
        num_beams = kwargs.get(
            "num_beams",
            generation_config.num_beams
            if hasattr(generation_config, "num_beams") and generation_config.num_beams is not None
            else 1,
        )
        if "assistant_model" in kwargs:
            # speculative decoding: the model should be able to return eos token
            generation_config.begin_suppress_tokens = None

        logits_processor = self._retrieve_logit_processors(
            generation_config=generation_config,
            logits_processor=logits_processor,
            begin_index=begin_index,  # begin index is index of first generated decoder token
            num_beams=num_beams,
            device=device,
        )

        # 4 Set and retrieve global generation variables
        self._set_condition_on_prev_tokens(
            condition_on_prev_tokens=condition_on_prev_tokens, generation_config=generation_config
        )

        temperatures = [temperature] if not isinstance(temperature, (list, tuple)) else temperature
        temperature = temperatures[0]

        max_frames, seek = self._retrieve_max_frames_and_seek(
            batch_size=batch_size,
            attention_mask=attention_mask,
            total_input_frames=total_input_frames,
            is_shortform=is_shortform,
        )

        # 5 Prepare running variables, list for generation
        num_return_sequences = generation_config.num_return_sequences
        (
            batch_idx_map,
            cur_bsz,
            input_features,
            seek,
            max_frames,
            init_tokens,
            do_condition_on_prev_tokens,
        ) = self._expand_variables_for_generation(
            input_features=input_features,
            seek=seek,
            max_frames=max_frames,
            init_tokens=init_tokens,
            batch_size=batch_size,
            condition_on_prev_tokens=condition_on_prev_tokens,
            generation_config=generation_config,
        )

        current_segments = self._prepare_segments(
            prompt_ids=prompt_ids,
            batch_size=cur_bsz,
            generation_config=generation_config,
        )
        # 5bis speculative decoding: ensure the assistant model does only one call to generate and therefore returns decoder input token ids and eos token id
        # we set a flag in the generation config to force the model to make only one call to generate and return the decoder input token ids and eos token id
        if "assistant_model" in kwargs:
            assistant_model = kwargs["assistant_model"]
            assistant_model.generation_config.force_unique_generate_call = True

        if force_unique_generate_call is None:
            if hasattr(generation_config, "force_unique_generate_call"):
                force_unique_generate_call = generation_config.force_unique_generate_call
            elif hasattr(self.generation_config, "force_unique_generate_call"):
                force_unique_generate_call = self.generation_config.force_unique_generate_call
            else:
                force_unique_generate_call = False

        # 6 Transcribe audio until we reach the end of all input audios
        while (seek < max_frames).any():
            if monitor_progress is not None:
                monitor_progress(torch.stack((seek, max_frames), dim=1))

            # 6.1 NOTE: When in longform transcription mode and batch size > 1 we need to dynamically reduce the batch size during the loop
            # in case one audio finished earlier than another one. Thus, we need to keep a table of "previous-index-2-current-index" in order
            # to know which original audio is being decoded
            # Set updated index map, duration of previously decoded chunks and number of max frames of current decoding chunk
            input_features, cur_bsz, batch_idx_map = self._maybe_reduce_batch(
                input_features=input_features,
                seek=seek,
                max_frames=max_frames,
                cur_bsz=cur_bsz,
                batch_idx_map=batch_idx_map,
            )
            time_offset = (
                seek.to(torch.float32 if device.type == "mps" else torch.float64) * time_precision / input_stride
            )
            seek_num_frames = (max_frames - seek).clamp(max=num_segment_frames)

            # 6.2 cut out next 30s segment from input features
            segment_input = self._get_input_segment(
                input_features=input_features,
                seek=seek,
                seek_num_frames=seek_num_frames,
                num_segment_frames=num_segment_frames,
                cur_bsz=cur_bsz,
                batch_idx_map=batch_idx_map,
            )

            # 6.3 prepare decoder input ids
            suppress_tokens = _get_attr_from_logit_processors(
                logits_processor, SuppressTokensLogitsProcessor, "suppress_tokens"
            )

            decoder_input_ids, kwargs = self._prepare_decoder_input_ids(
                cur_bsz=cur_bsz,
                init_tokens=init_tokens,
                current_segments=current_segments,
                batch_idx_map=batch_idx_map,
                do_condition_on_prev_tokens=do_condition_on_prev_tokens,
                prompt_ids=prompt_ids,
                generation_config=generation_config,
                config=self.config,
                device=init_tokens.device,
                suppress_tokens=suppress_tokens,
                timestamp_begin=timestamp_begin,
                kwargs=kwargs,
            )

            # 6.4 set max new tokens or max length
            self._set_max_new_tokens_and_length(
                config=self.config,
                decoder_input_ids=decoder_input_ids,
                generation_config=generation_config,
            )

            # 6.5 Set current `begin_index` for all logit processors
            if logits_processor is not None:
                for proc in logits_processor:
                    if hasattr(proc, "set_begin_index"):
                        proc.set_begin_index(decoder_input_ids.shape[-1])

            # 6.6 Run generate with fallback
            (
                seek_sequences,
                seek_outputs,
                should_skip,
                do_condition_on_prev_tokens,
                model_output_type,
            ) = self.generate_with_fallback(
                segment_input=segment_input,
                decoder_input_ids=decoder_input_ids,
                cur_bsz=cur_bsz,
                seek=seek,
                batch_idx_map=batch_idx_map,
                temperatures=temperatures,
                generation_config=generation_config,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
                prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
                synced_gpus=synced_gpus,
                return_token_timestamps=return_token_timestamps,
                do_condition_on_prev_tokens=do_condition_on_prev_tokens,
                is_shortform=is_shortform,
                batch_size=batch_size,
                attention_mask=attention_mask,
                kwargs=kwargs,
            )

            # 6.7 In every generated sequence, split by timestamp tokens and extract segments
            for i, seek_sequence in enumerate(seek_sequences):
                prev_i = batch_idx_map[i]

                if should_skip[i]:
                    seek[prev_i] += seek_num_frames[prev_i]
                    continue

                segments, segment_offset = self._retrieve_segment(
                    seek_sequence=seek_sequence,
                    seek_outputs=seek_outputs,
                    time_offset=time_offset,
                    timestamp_begin=timestamp_begin,
                    seek_num_frames=seek_num_frames,
                    time_precision=time_precision,
                    time_precision_features=time_precision_features,
                    input_stride=input_stride,
                    prev_idx=prev_i,
                    idx=i,
                    return_token_timestamps=return_token_timestamps,
                    decoder_input_ids=decoder_input_ids,
                )

                seek[prev_i] += segment_offset

                current_segments[prev_i] += segments

            if force_unique_generate_call:
                break

        # 7. Once all segments are added to the list of all segments, called `current_segments`, we extract the predicted
        # output tokens from the list of dicts. If we use batch size > 1, we make sure to pad the output
        final_segments = (
            [x[1:] for x in current_segments]
            if (prompt_ids is not None and generation_config.prompt_condition_type == "first-segment")
            else current_segments
        )

        # if return_dict_in_generate=True and we forced a unique call to generate or return_timestamps=False, meaning we are sure only one call to generate has been made,
        # -> we can return a ModelOutput
        # otherwise, return_dict_in_generate is applied in the 'result' of each segment in final_segments
        if (
            return_dict_in_generate
            and generation_config.return_dict_in_generate
            and (force_unique_generate_call or not return_timestamps)
        ):
            # only one call to generate_with_fallback, we can return a ModelOutput
            outputs = self._stack_split_outputs(seek_outputs, model_output_type, self.device, kwargs)
            if num_return_sequences > 1:
                if hasattr(outputs, "encoder_attentions") and outputs.encoder_attentions is not None:
                    outputs.encoder_attentions = tuple(
                        outputs.encoder_attentions[i][::num_return_sequences]
                        for i in range(len(outputs.encoder_attentions))
                    )
                if hasattr(outputs, "encoder_hidden_states") and outputs.encoder_hidden_states is not None:
                    outputs.encoder_hidden_states = tuple(
                        outputs.encoder_hidden_states[i][::num_return_sequences]
                        for i in range(len(outputs.encoder_hidden_states))
                    )
            return outputs

        padded_outputs = _pad_to_max_length(
            current_segments=final_segments,
            pad_token_id=generation_config.pad_token_id,
            device=self.device,
            padding_side="right",
            return_token_timestamps=return_token_timestamps,
            force_unique_generate_call=force_unique_generate_call,
        )

        if return_dict_in_generate and generation_config.return_dict_in_generate:
            logger.warning_once(
                "You have passed `return_dict_in_generate=True` and `return_timestamps=True`, this automatically sets `return_segments=True` to access the results of the underlying calls to GenerationMixin's generate in the returned `segments`."
            )
            return_segments = True
        elif not return_segments and not return_token_timestamps:
            return padded_outputs

        if return_token_timestamps:
            sequences, token_timestamps = padded_outputs
            outputs = {
                "sequences": sequences,
                "token_timestamps": token_timestamps,
            }
        else:
            sequences = padded_outputs
            outputs = {
                "sequences": sequences,
            }

        if return_segments:
            outputs["segments"] = final_segments

        return outputs
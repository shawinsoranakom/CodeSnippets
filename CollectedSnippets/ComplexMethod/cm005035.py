def decode(
        self,
        logits: np.ndarray,
        beam_width: int | None = None,
        beam_prune_logp: float | None = None,
        token_min_logp: float | None = None,
        hotwords: Iterable[str] | None = None,
        hotword_weight: float | None = None,
        alpha: float | None = None,
        beta: float | None = None,
        unk_score_offset: float | None = None,
        lm_score_boundary: bool | None = None,
        output_word_offsets: bool = False,
        n_best: int = 1,
    ):
        """
        Decode output logits to audio transcription with language model support.

        Args:
            logits (`np.ndarray`):
                The logits output vector of the model representing the log probabilities for each token.
            beam_width (`int`, *optional*):
                Maximum number of beams at each step in decoding. Defaults to pyctcdecode's DEFAULT_BEAM_WIDTH.
            beam_prune_logp (`int`, *optional*):
                A threshold to prune beams with log-probs less than best_beam_logp + beam_prune_logp. The value should
                be <= 0. Defaults to pyctcdecode's DEFAULT_PRUNE_LOGP.
            token_min_logp (`int`, *optional*):
                Tokens with log-probs below token_min_logp are skipped unless they are have the maximum log-prob for an
                utterance. Defaults to pyctcdecode's DEFAULT_MIN_TOKEN_LOGP.
            hotwords (`list[str]`, *optional*):
                List of words with extra importance which can be missing from the LM's vocabulary, e.g. ["huggingface"]
            hotword_weight (`int`, *optional*):
                Weight multiplier that boosts hotword scores. Defaults to pyctcdecode's DEFAULT_HOTWORD_WEIGHT.
            alpha (`float`, *optional*):
                Weight for language model during shallow fusion
            beta (`float`, *optional*):
                Weight for length score adjustment of during scoring
            unk_score_offset (`float`, *optional*):
                Amount of log score offset for unknown tokens
            lm_score_boundary (`bool`, *optional*):
                Whether to have kenlm respect boundaries when scoring
            output_word_offsets (`bool`, *optional*, defaults to `False`):
                Whether or not to output word offsets. Word offsets can be used in combination with the sampling rate
                and model downsampling rate to compute the time-stamps of transcribed words.
            n_best (`int`, *optional*, defaults to `1`):
                Number of best hypotheses to return. If `n_best` is greater than 1, the returned `text` will be a list
                of strings, `logit_score` will be a list of floats, and `lm_score` will be a list of floats, where the
                length of these lists will correspond to the number of returned hypotheses. The value should be >= 1.

                <Tip>

                Please take a look at the example below to better understand how to make use of `output_word_offsets`.

                </Tip>

        Returns:
            [`~models.wav2vec2.Wav2Vec2DecoderWithLMOutput`].

        Example:

        ```python
        >>> # Let's see how to retrieve time steps for a model
        >>> from transformers import AutoTokenizer, AutoProcessor, AutoModelForCTC
        >>> from datasets import load_dataset
        >>> import datasets
        >>> import torch

        >>> # import model, feature extractor, tokenizer
        >>> model = AutoModelForCTC.from_pretrained("patrickvonplaten/wav2vec2-base-100h-with-lm")
        >>> processor = AutoProcessor.from_pretrained("patrickvonplaten/wav2vec2-base-100h-with-lm")

        >>> # load first sample of English common_voice
        >>> dataset = load_dataset("mozilla-foundation/common_voice_11_0", "en", split="train", streaming=True)
        >>> dataset = dataset.cast_column("audio", datasets.Audio(sampling_rate=16_000))
        >>> dataset_iter = iter(dataset)
        >>> sample = next(dataset_iter)

        >>> # forward sample through model to get greedily predicted transcription ids
        >>> input_values = processor(sample["audio"]["array"], return_tensors="pt").input_values
        >>> with torch.no_grad():
        ...     logits = model(input_values).logits[0].cpu().numpy()

        >>> # retrieve word stamps (analogous commands for `output_char_offsets`)
        >>> outputs = processor.decode(logits, output_word_offsets=True)
        >>> # compute `time_offset` in seconds as product of downsampling ratio and sampling_rate
        >>> time_offset = model.config.inputs_to_logits_ratio / processor.feature_extractor.sampling_rate

        >>> word_offsets = [
        ...     {
        ...         "word": d["word"],
        ...         "start_time": round(d["start_offset"] * time_offset, 2),
        ...         "end_time": round(d["end_offset"] * time_offset, 2),
        ...     }
        ...     for d in outputs.word_offsets
        ... ]
        >>> # compare word offsets with audio `en_train_0/common_voice_en_19121553.mp3` online on the dataset viewer:
        >>> # https://huggingface.co/datasets/mozilla-foundation/common_voice_11_0/viewer/en
        >>> word_offsets[:4]
        [{'word': 'THE', 'start_time': 0.68, 'end_time': 0.78}, {'word': 'TRACK', 'start_time': 0.88, 'end_time': 1.1}, {'word': 'APPEARS', 'start_time': 1.18, 'end_time': 1.66}, {'word': 'ON', 'start_time': 1.86, 'end_time': 1.92}]
        ```"""

        from pyctcdecode.constants import (
            DEFAULT_BEAM_WIDTH,
            DEFAULT_HOTWORD_WEIGHT,
            DEFAULT_MIN_TOKEN_LOGP,
            DEFAULT_PRUNE_LOGP,
        )

        # set defaults
        beam_width = beam_width if beam_width is not None else DEFAULT_BEAM_WIDTH
        beam_prune_logp = beam_prune_logp if beam_prune_logp is not None else DEFAULT_PRUNE_LOGP
        token_min_logp = token_min_logp if token_min_logp is not None else DEFAULT_MIN_TOKEN_LOGP
        hotword_weight = hotword_weight if hotword_weight is not None else DEFAULT_HOTWORD_WEIGHT

        # reset params at every forward call. It's just a `set` method in pyctcdecode
        self.decoder.reset_params(
            alpha=alpha, beta=beta, unk_score_offset=unk_score_offset, lm_score_boundary=lm_score_boundary
        )

        # pyctcdecode
        decoded_beams = self.decoder.decode_beams(
            logits,
            beam_width=beam_width,
            beam_prune_logp=beam_prune_logp,
            token_min_logp=token_min_logp,
            hotwords=hotwords,
            hotword_weight=hotword_weight,
        )

        word_offsets = None
        if output_word_offsets:
            word_offsets = [
                [
                    {"word": word, "start_offset": start_offset, "end_offset": end_offset}
                    for word, (start_offset, end_offset) in beam[2]
                ]
                for beam in decoded_beams
            ]
        logit_scores = [beam[-2] for beam in decoded_beams]

        lm_scores = [beam[-1] for beam in decoded_beams]

        hypotheses = [beam[0] for beam in decoded_beams]

        if n_best > len(decoded_beams):
            logger.info(
                "N-best size is larger than the number of generated hypotheses, all hypotheses will be returned."
            )

        if n_best == 1:
            return Wav2Vec2DecoderWithLMOutput(
                text=hypotheses[0],
                logit_score=logit_scores[0],
                lm_score=lm_scores[0],
                word_offsets=word_offsets[0] if word_offsets is not None else None,
            )
        else:
            return Wav2Vec2DecoderWithLMOutput(
                text=hypotheses[:n_best],
                logit_score=logit_scores[:n_best],
                lm_score=lm_scores[:n_best],
                word_offsets=word_offsets[:n_best] if word_offsets is not None else None,
            )
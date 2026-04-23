def batch_decode(
        self,
        logits: np.ndarray,
        pool: Pool | None = None,
        num_processes: int | None = None,
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
        Batch decode output logits to audio transcription with language model support.

        <Tip>

        This function makes use of Python's multiprocessing. Currently, multiprocessing is available only on Unix
        systems (see this [issue](https://github.com/kensho-technologies/pyctcdecode/issues/65)).

        If you are decoding multiple batches, consider creating a `Pool` and passing it to `batch_decode`. Otherwise,
        `batch_decode` will be very slow since it will create a fresh `Pool` for each call. See usage example below.

        </Tip>

        Args:
            logits (`np.ndarray`):
                The logits output vector of the model representing the log probabilities for each token.
            pool (`multiprocessing.Pool`, *optional*):
                An optional user-managed pool. If not set, one will be automatically created and closed. The pool
                should be instantiated *after* `Wav2Vec2ProcessorWithLM`. Otherwise, the LM won't be available to the
                pool's sub-processes.

                <Tip>

                Currently, only pools created with a 'fork' context can be used. If a 'spawn' pool is passed, it will
                be ignored and sequential decoding will be used instead.

                </Tip>

            num_processes (`int`, *optional*):
                If `pool` is not set, number of processes on which the function should be parallelized over. Defaults
                to the number of available CPUs.
            beam_width (`int`, *optional*):
                Maximum number of beams at each step in decoding. Defaults to pyctcdecode's DEFAULT_BEAM_WIDTH.
            beam_prune_logp (`int`, *optional*):
                Beams that are much worse than best beam will be pruned Defaults to pyctcdecode's DEFAULT_PRUNE_LOGP.
            token_min_logp (`int`, *optional*):
                Tokens below this logp are skipped unless they are argmax of frame Defaults to pyctcdecode's
                DEFAULT_MIN_TOKEN_LOGP.
            hotwords (`list[str]`, *optional*):
                List of words with extra importance, can be OOV for LM
            hotword_weight (`int`, *optional*):
                Weight factor for hotword importance Defaults to pyctcdecode's DEFAULT_HOTWORD_WEIGHT.
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
                of lists of strings, `logit_score` will be a list of lists of floats, and `lm_score` will be a list of
                lists of floats, where the length of the outer list will correspond to the batch size and the length of
                the inner list will correspond to the number of returned hypotheses . The value should be >= 1.

                <Tip>

                Please take a look at the Example of [`~Wav2Vec2ProcessorWithLM.decode`] to better understand how to
                make use of `output_word_offsets`. [`~Wav2Vec2ProcessorWithLM.batch_decode`] works the same way with
                batched output.

                </Tip>

        Returns:
            [`~models.wav2vec2.Wav2Vec2DecoderWithLMOutput`].

        Example:
            See [Decoding multiple audios](#decoding-multiple-audios).
        """

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

        # create multiprocessing pool and list numpy arrays
        # filter out logits padding
        logits_list = [array[(array != -100.0).all(axis=-1)] for array in logits]

        # create a pool if necessary while also using it as a context manager to close itself
        if pool is None:
            # fork is safe to use only on Unix, see "Contexts and start methods" section on
            # multiprocessing's docs (https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods)
            default_context = get_start_method()

            if default_context == "fork":
                cm = pool = get_context().Pool(num_processes)
            else:
                logger.warning(
                    "Parallel batch decoding is not currently supported in this platform. "
                    "Falling back to sequential decoding."
                )
                cm = nullcontext()
        else:
            # pool is managed by the user, so we don't need to close it
            cm = nullcontext()

            if num_processes is not None:
                logger.warning(
                    "Parameter `num_process` was passed, but it will be ignored since `pool` was also specified."
                )

        # pyctcdecode
        with cm:
            decoded_beams = self.decoder.decode_beams_batch(
                pool=pool,
                logits_list=logits_list,
                beam_width=beam_width,
                beam_prune_logp=beam_prune_logp,
                token_min_logp=token_min_logp,
                hotwords=hotwords,
                hotword_weight=hotword_weight,
            )

        # extract text and scores
        batch_texts, logit_scores, lm_scores, word_offsets = [], [], [], []

        for d in decoded_beams:
            batch_texts.append([beam[0] for beam in d])
            logit_scores.append([beam[-2] for beam in d])
            lm_scores.append([beam[-1] for beam in d])

            # word_offsets.append([{"word": t[0], "start_offset": t[1][0], "end_offset": t[1][1]} for t in d[0][1]])

            word_offsets.append(
                [
                    [
                        {"word": word, "start_offset": start_offset, "end_offset": end_offset}
                        for word, (start_offset, end_offset) in beam[1]
                    ]
                    for beam in d
                ]
            )

        word_offsets = word_offsets if output_word_offsets else None

        if n_best == 1:
            return Wav2Vec2DecoderWithLMOutput(
                text=[hyps[0] for hyps in batch_texts],
                logit_score=[hyps[0] for hyps in logit_scores],
                lm_score=[hyps[0] for hyps in lm_scores],
                word_offsets=[hyps[0] for hyps in word_offsets] if word_offsets is not None else None,
            )
        else:
            return Wav2Vec2DecoderWithLMOutput(
                text=[hyps[:n_best] for hyps in batch_texts],
                logit_score=[hyps[:n_best] for hyps in logit_scores],
                lm_score=[hyps[:n_best] for hyps in lm_scores],
                word_offsets=[hyps[:n_best] for hyps in word_offsets] if word_offsets is not None else None,
            )
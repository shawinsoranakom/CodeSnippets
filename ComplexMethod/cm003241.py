def _need_fallback(
        self,
        seek_sequence,
        seek_outputs,
        index,
        logits_processor,
        generation_config,
        vocab_size,
        temperature,
    ):
        needs_fallback = False
        should_skip = False
        if generation_config.compression_ratio_threshold is not None:
            compression_ratio = self._retrieve_compression_ratio(seek_sequence, vocab_size)

            if compression_ratio > generation_config.compression_ratio_threshold:
                needs_fallback = True

        if generation_config.logprob_threshold is not None:
            if hasattr(seek_outputs[0], "sequences_scores"):
                logprobs = [s["sequences_scores"] for s in seek_outputs][index]
            else:
                scores = seek_outputs[index]["scores"]
                logprobs = self._retrieve_avg_logprobs(
                    scores,
                    seek_sequence,
                    temperature,
                )

            if logprobs < generation_config.logprob_threshold:
                needs_fallback = True

        if generation_config.no_speech_threshold is not None:
            no_speech_prob = _get_attr_from_logit_processors(
                logits_processor, WhisperNoSpeechDetection, "no_speech_prob"
            )

            if (
                logprobs < generation_config.logprob_threshold
                and no_speech_prob[index] > generation_config.no_speech_threshold
            ):
                needs_fallback = False
                should_skip = True

        return needs_fallback, should_skip
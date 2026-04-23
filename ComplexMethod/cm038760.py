def sample(
        self,
        tokenizer: TokenizerLike,
        num_requests: int,
        request_id_prefix: str = "",
        no_oversample: bool = False,
        output_len: int | None = None,
        **kwargs,
    ) -> list[SampleRequest]:
        output_len = output_len if output_len is not None else self.DEFAULT_OUTPUT_LEN
        if "openai" in getattr(tokenizer, "name_or_path", ""):
            prompt = "<|startoftranscript|><|en|><|transcribe|><|notimestamps|>"
        else:
            prompt = ""
        prompt_len = len(tokenizer(prompt).input_ids)
        sampled_requests: list[SampleRequest] = []
        ind = 0
        skipped = 0
        asr_min_audio_len_sec = kwargs.get("asr_min_audio_len_sec")
        asr_max_audio_len_sec = kwargs.get("asr_max_audio_len_sec")
        durations = []
        for item in self.data:
            if len(sampled_requests) >= num_requests:
                break
            audio = item["audio"]
            y, sr = audio["array"], audio["sampling_rate"]
            duration_s = get_audio_duration(y=y, sr=sr)
            if duration_s < asr_min_audio_len_sec or duration_s > asr_max_audio_len_sec:
                skipped += 1
                continue

            durations.append(duration_s)
            mm_content = {"audio": (y, sr)}
            sampled_requests.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=prompt_len,
                    expected_output_len=output_len,
                    multi_modal_data=mm_content,
                    request_id=request_id_prefix + str(ind),
                )
            )
            ind += 1
        if skipped:
            logger.warning(
                "%d samples discarded from dataset due to"
                " their length being greater than"
                " what Whisper supports.",
                skipped,
            )

        logger.info("Number of audio samples: %d", len(durations))
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        median_duration = np.median(durations) if durations else 0
        logger.info(
            "Audio duration statistics (s): avg=%.2f, min=%.2f, max=%.2f, median=%.2f",
            avg_duration,
            min_duration,
            max_duration,
            median_duration,
        )

        self.maybe_oversample_requests(
            sampled_requests, num_requests, request_id_prefix, no_oversample
        )
        return sampled_requests
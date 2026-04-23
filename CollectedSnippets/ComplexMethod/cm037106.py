def _preprocess_audio(
        self,
        text: list[str],
        audios: list[npt.NDArray],
    ) -> tuple[list[str], dict[str, Any]]:
        if len(audios) == 0:
            return text, {"audio_num_clips": []}

        assert self.audio_extractor is not None
        extractor = self.audio_extractor

        parts = [x for x in re.split(f"({re.escape(AUDIO_CONTEXT)})", text[0]) if x]
        token_count = parts.count(AUDIO_CONTEXT)
        if token_count != len(audios):
            raise ValueError(
                "Number of audio tokens in text does not match the number "
                f"of audios (tokens={token_count}, audios={len(audios)})."
            )
        audio_index = 0
        for idx, part in enumerate(parts):
            if part == AUDIO_CONTEXT:
                audio_repl = self.get_audio_repl(audios[audio_index])
                parts[idx] = audio_repl.full
                audio_index += 1
        text = ["".join(parts)]
        audio_inputs = extractor(audios)
        return text, audio_inputs
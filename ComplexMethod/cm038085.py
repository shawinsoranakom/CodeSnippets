def get_mm_max_tokens_per_item(
        self,
        seq_len: int,
        mm_counts: Mapping[str, int] | None = None,
    ) -> Mapping[str, int] | None:
        mm_counts = mm_counts or {}
        requested_modalities = {m for m, c in mm_counts.items() if c > 0}
        mm_max_tokens: dict[str, int] = {}

        if requested_modalities & {"image", "video"}:
            vl_tokens = Qwen2_5_VLProcessingInfo.get_mm_max_tokens_per_item(
                self,
                seq_len=seq_len,
                mm_counts=mm_counts,
            )
            mm_max_tokens.update(
                {
                    m: vl_tokens[m]
                    for m in ["image", "video"]
                    if m in requested_modalities
                }
            )

        if "audio" in requested_modalities:
            audio_tokens = Qwen2AudioProcessingInfo.get_mm_max_tokens_per_item(
                self,
                seq_len=seq_len,
                mm_counts=mm_counts,
            )
            mm_max_tokens["audio"] = audio_tokens["audio"]

        return mm_max_tokens
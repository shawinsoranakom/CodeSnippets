def _resolve_audio_columns(self, dataset, custom_format_mapping: dict = None):
        """Resolve audio, text, and speaker columns from user mapping or hardcoded fallback.

        Returns:
            dict with keys: audio_col, text_col, speaker_col (speaker_col may be None)
        """
        cols = dataset.column_names

        if custom_format_mapping:
            audio_col = None
            text_col = None
            speaker_col = None
            for col, role in custom_format_mapping.items():
                if role == "audio":
                    audio_col = col
                elif role == "text":
                    text_col = col
                elif role == "speaker_id":
                    speaker_col = col
            # Use mapping if both required columns exist in the dataset
            if audio_col and audio_col in cols and text_col and text_col in cols:
                return {
                    "audio_col": audio_col,
                    "text_col": text_col,
                    "speaker_col": speaker_col,
                }

        # Hardcoded fallback (existing behavior)
        audio_col = next((c for c in cols if c.lower() in ("audio", "speech")), None)
        text_col = next(
            (
                c
                for c in cols
                if c.lower() in ("text", "sentence", "transcript", "transcription")
            ),
            None,
        )

        speaker_col = None
        if "source" in cols:
            speaker_col = "source"
        elif "speaker_id" in cols:
            speaker_col = "speaker_id"

        return {
            "audio_col": audio_col,
            "text_col": text_col,
            "speaker_col": speaker_col,
        }
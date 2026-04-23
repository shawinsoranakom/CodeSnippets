def _reassemble_chunk_texts(
        texts: list[str],
        audio_chunk_index: list[tuple[int, int | None]],
        separator: str = " ",
    ) -> list[str]:
        """Reassemble per-chunk transcription texts back into per-sample strings.

        When audio inputs are longer than the feature extractor's `max_audio_clip_s`, they are split into
        overlapping chunks before being fed to the model. This means a single original audio sample can
        produce multiple decoded text segments. This method reverses that chunking: it groups the decoded
        texts by their original sample index using `chunk_map`, orders the chunks, and joins them
        with `separator` to reconstruct one transcription string per input sample.

        Args:
            texts: Decoded text strings, one per model output (i.e. one per chunk).
            audio_chunk_index: List of `(sample_idx, chunk_idx)` tuples that map each entry in
                `texts` back to its original sample and chunk position. A `chunk_idx` of `None`
                indicates the sample was not chunked.
            separator: String used to join chunks belonging to the same sample. Defaults to a
                space; callers pass an empty string for languages that don't use spaces between
                words (e.g. Chinese, Japanese).

        Returns:
            A list of reassembled transcription strings, one per original input sample.
        """
        max_sample_idx = max(sample_idx for sample_idx, _ in audio_chunk_index)
        outputs = [""] * (max_sample_idx + 1)
        chunked = {}

        for (sample_idx, chunk_idx), text in zip(audio_chunk_index, texts):
            if chunk_idx is None:
                outputs[sample_idx] = text
            else:
                if sample_idx not in chunked:
                    chunked[sample_idx] = []
                chunked[sample_idx].append((chunk_idx, text))

        for sample_idx, chunk_items in chunked.items():
            chunk_items.sort(key=lambda item: item[0])
            non_empty = [t for _, t in chunk_items if t and t.strip()]
            parts = [non_empty[0].rstrip()] + [t.strip() for t in non_empty[1:]]
            outputs[sample_idx] = separator.join(parts)

        return outputs
def _trim_rich_text_segments(segments: list[dict]) -> list[dict]:
        trimmed_segments = [dict(segment) for segment in segments if segment.get("text") is not None]
        if not trimmed_segments:
            return []

        start_idx = 0
        while start_idx < len(trimmed_segments):
            normalized_text = trimmed_segments[start_idx]["text"].lstrip()
            if normalized_text:
                trimmed_segments[start_idx]["text"] = normalized_text
                break
            start_idx += 1

        if start_idx == len(trimmed_segments):
            return []

        trimmed_segments = trimmed_segments[start_idx:]
        end_idx = len(trimmed_segments) - 1
        while end_idx >= 0:
            normalized_text = trimmed_segments[end_idx]["text"].rstrip()
            if normalized_text:
                trimmed_segments[end_idx]["text"] = normalized_text
                break
            end_idx -= 1

        if end_idx < 0:
            return []

        return trimmed_segments[:end_idx + 1]
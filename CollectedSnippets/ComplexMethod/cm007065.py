def _word_count(self, text: str) -> dict[str, Any]:
        """Count words, characters, and lines in text."""
        result: dict[str, Any] = {}

        # Handle empty or whitespace-only text - return zeros
        text_str = str(text) if text else ""
        is_empty = not text_str or not text_str.strip()

        if getattr(self, "count_words", True):
            if is_empty:
                result["word_count"] = 0
                result["unique_words"] = 0
            else:
                words = text_str.split()
                result["word_count"] = len(words)
                result["unique_words"] = len(set(words))

        if getattr(self, "count_characters", True):
            if is_empty:
                result["character_count"] = 0
                result["character_count_no_spaces"] = 0
            else:
                result["character_count"] = len(text_str)
                result["character_count_no_spaces"] = len(text_str.replace(" ", ""))

        if getattr(self, "count_lines", True):
            if is_empty:
                result["line_count"] = 0
                result["non_empty_lines"] = 0
            else:
                lines = text_str.split("\n")
                result["line_count"] = len(lines)
                result["non_empty_lines"] = len([line for line in lines if line.strip()])

        return result
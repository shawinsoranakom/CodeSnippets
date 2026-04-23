def _text_chars(self, length, truncate, text):
        """Truncate a string after a certain number of chars."""
        truncate_len = calculate_truncate_chars_length(length, truncate)
        s_len = 0
        end_index = None
        for i, char in enumerate(text):
            if unicodedata.combining(char):
                # Don't consider combining characters
                # as adding to the string length
                continue
            s_len += 1
            if end_index is None and s_len > truncate_len:
                end_index = i
            if s_len > length:
                # Return the truncated string
                return add_truncation_text(text[: end_index or 0], truncate)

        # Return the original string since no truncation was necessary
        return text
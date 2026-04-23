def _text_words(self, length, truncate):
        """
        Truncate a string after a certain number of words.

        Strip newlines in the string.
        """
        words = self._wrapped.split()
        if len(words) > length:
            words = words[:length]
            return add_truncation_text(" ".join(words), truncate)
        return " ".join(words)
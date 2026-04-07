def chars(self, num, truncate=None, html=False):
        """
        Return the text truncated to be no longer than the specified number
        of characters.

        `truncate` specifies what should be used to notify that the string has
        been truncated, defaulting to a translatable string of an ellipsis.
        """
        self._setup()
        length = int(num)
        if length <= 0:
            return ""
        text = unicodedata.normalize("NFC", self._wrapped)

        if html:
            parser = TruncateCharsHTMLParser(length=length, replacement=truncate)
            parser.feed(text)
            parser.close()
            return "".join(parser.output)
        return self._text_chars(length, truncate, text)
def words(self, num, truncate=None, html=False):
        """
        Truncate a string after a certain number of words. `truncate` specifies
        what should be used to notify that the string has been truncated,
        defaulting to ellipsis.
        """
        self._setup()
        length = int(num)
        if length <= 0:
            return ""
        if html:
            parser = TruncateWordsHTMLParser(length=length, replacement=truncate)
            parser.feed(self._wrapped)
            parser.close()
            return "".join(parser.output)
        return self._text_words(length, truncate)
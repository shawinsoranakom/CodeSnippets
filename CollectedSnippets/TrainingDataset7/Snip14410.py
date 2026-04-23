def writeString(self, encoding):
        """
        Return the feed in the given encoding as a string.
        """
        s = StringIO()
        self.write(s, encoding)
        return s.getvalue()
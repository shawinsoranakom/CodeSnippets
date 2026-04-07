def getvalue(self):
        """
        Return the fully serialized queryset (or None if the output stream is
        not seekable).
        """
        if callable(getattr(self.stream, "getvalue", None)):
            return self.stream.getvalue()
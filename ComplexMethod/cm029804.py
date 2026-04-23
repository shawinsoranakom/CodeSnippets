def write(self, s):
        'Write data, where s is a str'
        if self.closed:
            raise ValueError("write to closed file")
        if not isinstance(s, str):
            raise TypeError("can't write %s to text stream" %
                            s.__class__.__name__)
        length = len(s)
        haslf = (self._writetranslate or self._line_buffering) and "\n" in s
        if haslf and self._writetranslate and self._writenl != "\n":
            s = s.replace("\n", self._writenl)
        encoder = self._encoder or self._get_encoder()
        # XXX What if we were just reading?
        b = encoder.encode(s)
        self.buffer.write(b)
        if self._line_buffering and (haslf or "\r" in s):
            self.flush()
        if self._snapshot is not None:
            self._set_decoded_chars('')
            self._snapshot = None
        if self._decoder:
            self._decoder.reset()
        return length
def unget(self, bytes):
        """
        Place bytes back onto the front of the lazy stream.

        Future calls to read() will return those bytes first. The
        stream position and thus tell() will be rewound.
        """
        if not bytes:
            return
        self._update_unget_history(len(bytes))
        self.position -= len(bytes)
        self._leftover = bytes + self._leftover
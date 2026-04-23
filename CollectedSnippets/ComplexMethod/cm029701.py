def connect(self, host='localhost', port=0, source_address=None):
        """Connect to the LMTP daemon, on either a Unix or a TCP socket."""
        if host[0] != '/':
            return super().connect(host, port, source_address=source_address)

        if self.timeout is not None and not self.timeout:
            raise ValueError('Non-blocking socket (timeout=0) is not supported')

        # Handle Unix-domain sockets.
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                self.sock.settimeout(self.timeout)
            self.file = None
            self.sock.connect(host)
        except OSError:
            if self.debuglevel > 0:
                self._print_debug('connect fail:', host)
            if self.sock:
                self.sock.close()
            self.sock = None
            raise
        (code, msg) = self.getreply()
        if self.debuglevel > 0:
            self._print_debug('connect:', msg)
        return (code, msg)
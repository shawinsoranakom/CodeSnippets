def _readline(self):
        if self.sigint_received:
            # There's a pending unhandled SIGINT. Handle it now.
            self.sigint_received = False
            raise KeyboardInterrupt

        # Wait for either a SIGINT or a line or EOF from the PDB server.
        selector = selectors.DefaultSelector()
        selector.register(self.signal_read, selectors.EVENT_READ)
        selector.register(self.server_socket, selectors.EVENT_READ)

        while b"\n" not in self.read_buf:
            for key, _ in selector.select():
                if key.fileobj == self.signal_read:
                    self.signal_read.recv(1024)
                    if self.sigint_received:
                        # If not, we're reading wakeup events for sigints that
                        # we've previously handled, and can ignore them.
                        self.sigint_received = False
                        raise KeyboardInterrupt
                elif key.fileobj == self.server_socket:
                    data = self.server_socket.recv(16 * 1024)
                    self.read_buf += data
                    if not data and b"\n" not in self.read_buf:
                        # EOF without a full final line. Drop the partial line.
                        self.read_buf = b""
                        return b""

        ret, sep, self.read_buf = self.read_buf.partition(b"\n")
        return ret + sep
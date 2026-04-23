def handle(self):
        # Send a welcome message.
        self._send_textline('* OK IMAP4rev1')
        while 1:
            # Gather up input until we receive a line terminator or we timeout.
            # Accumulate read(1) because it's simpler to handle the differences
            # between naked sockets and SSL sockets.
            line = b''
            while 1:
                try:
                    part = self.rfile.read(1)
                    if part == b'':
                        # Naked sockets return empty strings..
                        return
                    line += part
                except OSError:
                    # ..but SSLSockets raise exceptions.
                    return
                if line.endswith(b'\r\n'):
                    break

            if verbose:
                print('GOT: %r' % line.strip())
            if self.continuation:
                try:
                    self.continuation.send(line)
                except StopIteration:
                    self.continuation = None
                continue
            splitline = line.decode('ASCII').split()
            tag = splitline[0]
            cmd = splitline[1]
            args = splitline[2:]

            if hasattr(self, 'cmd_' + cmd):
                continuation = getattr(self, 'cmd_' + cmd)(tag, args)
                if continuation:
                    self.continuation = continuation
                    next(continuation)
            else:
                self._send_tagged(tag, 'BAD', cmd + ' unknown')
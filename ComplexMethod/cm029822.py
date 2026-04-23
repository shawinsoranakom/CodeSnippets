def _install_message(self, message):
        """Format a message and blindly write to self._file."""
        from_line = None
        if isinstance(message, str):
            message = self._string_to_bytes(message)
        if isinstance(message, bytes) and message.startswith(b'From '):
            newline = message.find(b'\n')
            if newline != -1:
                from_line = message[:newline]
                message = message[newline + 1:]
            else:
                from_line = message
                message = b''
        elif isinstance(message, _mboxMMDFMessage):
            author = message.get_from().encode('ascii')
            from_line = b'From ' + author
        elif isinstance(message, email.message.Message):
            from_line = message.get_unixfrom()  # May be None.
            if from_line is not None:
                from_line = from_line.encode('ascii')
        if from_line is None:
            from_line = b'From MAILER-DAEMON ' + time.asctime(time.gmtime()).encode()
        start = self._file.tell()
        self._file.write(from_line + linesep)
        self._dump_message(message, self._file, self._mangle_from_)
        stop = self._file.tell()
        return (start, stop)
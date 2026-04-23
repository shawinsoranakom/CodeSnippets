def _get_response(self, start_timeout=False):

        # Read response and store.
        #
        # Returns None for continuation responses,
        # otherwise first response line received.
        #
        # If start_timeout is given, temporarily uses it as a socket
        # timeout while waiting for the start of a response, raising
        # _responsetimeout if one doesn't arrive. (Used by Idler.)

        if start_timeout is not False and self.sock:
            assert start_timeout is None or start_timeout > 0
            saved_timeout = self.sock.gettimeout()
            self.sock.settimeout(start_timeout)
            try:
                resp = self._get_line()
            except TimeoutError as err:
                raise self._responsetimeout from err
            finally:
                self.sock.settimeout(saved_timeout)
        else:
            resp = self._get_line()

        # Command completion response?

        if self._match(self.tagre, resp):
            tag = self.mo.group('tag')
            if not tag in self.tagged_commands:
                raise self.abort('unexpected tagged response: %r' % resp)

            typ = self.mo.group('type')
            typ = str(typ, self._encoding)
            dat = self.mo.group('data')
            self.tagged_commands[tag] = (typ, [dat])
        else:
            dat2 = None

            # '*' (untagged) responses?

            if not self._match(Untagged_response, resp):
                if self._match(self.Untagged_status, resp):
                    dat2 = self.mo.group('data2')

            if self.mo is None:
                # Only other possibility is '+' (continuation) response...

                if self._match(Continuation, resp):
                    self.continuation_response = self.mo.group('data')
                    return None     # NB: indicates continuation

                raise self.abort("unexpected response: %r" % resp)

            typ = self.mo.group('type')
            typ = str(typ, self._encoding)
            dat = self.mo.group('data')
            if dat is None: dat = b''        # Null untagged response
            if dat2: dat = dat + b' ' + dat2

            # Is there a literal to come?

            while self._match(self.Literal, dat):

                # Read literal direct from connection.

                size = int(self.mo.group('size'))
                if __debug__:
                    if self.debug >= 4:
                        self._mesg('read literal size %s' % size)
                data = self.read(size)

                # Store response with literal as tuple

                self._append_untagged(typ, (dat, data))

                # Read trailer - possibly containing another literal

                dat = self._get_line()

            self._append_untagged(typ, dat)

        # Bracketed response information?

        if typ in ('OK', 'NO', 'BAD') and self._match(Response_code, dat):
            typ = self.mo.group('type')
            typ = str(typ, self._encoding)
            self._append_untagged(typ, self.mo.group('data'))

        if __debug__:
            if self.debug >= 1 and typ in ('NO', 'BAD', 'BYE'):
                self._mesg('%s response: %r' % (typ, dat))

        return resp
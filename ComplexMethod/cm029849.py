def _append_untagged(self, typ, dat):
        if dat is None:
            dat = b''

        # During idle, queue untagged responses for delivery via iteration
        if self._idle_capture:
            # Responses containing literal strings are passed to us one data
            # fragment at a time, while others arrive in a single call.
            if (not self._idle_responses or
                isinstance(self._idle_responses[-1][1][-1], bytes)):
                # We are not continuing a fragmented response; start a new one
                self._idle_responses.append((typ, [dat]))
            else:
                # We are continuing a fragmented response; append the fragment
                response = self._idle_responses[-1]
                assert response[0] == typ
                response[1].append(dat)
            if __debug__ and self.debug >= 5:
                self._mesg(f'idle: queue untagged {typ} {dat!r}')
            return

        ur = self.untagged_responses
        if __debug__:
            if self.debug >= 5:
                self._mesg('untagged_responses[%s] %s += ["%r"]' %
                        (typ, len(ur.get(typ,'')), dat))
        if typ in ur:
            ur[typ].append(dat)
        else:
            ur[typ] = [dat]
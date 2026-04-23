def _parse_headers(self, lines):
        # Passed a list of lines that make up the headers for the current msg
        lastheader = ''
        lastvalue = []
        for lineno, line in enumerate(lines):
            # Check for continuation
            if line[0] in ' \t':
                if not lastheader:
                    # The first line of the headers was a continuation.  This
                    # is illegal, so let's note the defect, store the illegal
                    # line, and ignore it for purposes of headers.
                    defect = errors.FirstHeaderLineIsContinuationDefect(line)
                    self.policy.handle_defect(self._cur, defect)
                    continue
                lastvalue.append(line)
                continue
            if lastheader:
                self._cur.set_raw(*self.policy.header_source_parse(lastvalue))
                lastheader, lastvalue = '', []
            # Check for envelope header, i.e. unix-from
            if line.startswith('From '):
                if lineno == 0:
                    # Strip off the trailing newline
                    mo = NLCRE_eol.search(line)
                    if mo:
                        line = line[:-len(mo.group(0))]
                    self._cur.set_unixfrom(line)
                    continue
                elif lineno == len(lines) - 1:
                    # Something looking like a unix-from at the end - it's
                    # probably the first line of the body, so push back the
                    # line and stop.
                    self._input.unreadline(line)
                    return
                else:
                    # Weirdly placed unix-from line.
                    defect = errors.MisplacedEnvelopeHeaderDefect(line)
                    self.policy.handle_defect(self._cur, defect)
                    continue
            # Split the line on the colon separating field name from value.
            # There will always be a colon, because if there wasn't the part of
            # the parser that calls us would have started parsing the body.
            i = line.find(':')

            # If the colon is on the start of the line the header is clearly
            # malformed, but we might be able to salvage the rest of the
            # message. Track the error but keep going.
            if i == 0:
                defect = errors.InvalidHeaderDefect("Missing header name.")
                self.policy.handle_defect(self._cur, defect)
                continue

            assert i>0, "_parse_headers fed line with no : and no leading WS"
            lastheader = line[:i]
            lastvalue = [line]
        # Done with all the lines, so handle the last header.
        if lastheader:
            self._cur.set_raw(*self.policy.header_source_parse(lastvalue))
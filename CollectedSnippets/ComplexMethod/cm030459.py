def _parsegen(self):
        # Create a new message and start by parsing headers.
        self._new_message()
        headers = []
        # Collect the headers, searching for a line that doesn't match the RFC
        # 2822 header or continuation pattern (including an empty line).
        for line in self._input:
            if line is NeedMoreData:
                yield NeedMoreData
                continue
            if not headerRE.match(line):
                # If we saw the RFC defined header/body separator
                # (i.e. newline), just throw it away. Otherwise the line is
                # part of the body so push it back.
                if not NLCRE.match(line):
                    defect = errors.MissingHeaderBodySeparatorDefect()
                    self.policy.handle_defect(self._cur, defect)
                    self._input.unreadline(line)
                break
            headers.append(line)
        # Done with the headers, so parse them and figure out what we're
        # supposed to see in the body of the message.
        self._parse_headers(headers)
        # Headers-only parsing is a backwards compatibility hack, which was
        # necessary in the older parser, which could raise errors.  All
        # remaining lines in the input are thrown into the message body.
        if self._headersonly:
            lines = []
            while True:
                line = self._input.readline()
                if line is NeedMoreData:
                    yield NeedMoreData
                    continue
                if line == '':
                    break
                lines.append(line)
            self._cur.set_payload(EMPTYSTRING.join(lines))
            return
        if self._cur.get_content_type() == 'message/delivery-status':
            # message/delivery-status contains blocks of headers separated by
            # a blank line.  We'll represent each header block as a separate
            # nested message object, but the processing is a bit different
            # than standard message/* types because there is no body for the
            # nested messages.  A blank line separates the subparts.
            while True:
                self._input.push_eof_matcher(NLCRE.match)
                for retval in self._parsegen():
                    if retval is NeedMoreData:
                        yield NeedMoreData
                        continue
                    break
                self._pop_message()
                # We need to pop the EOF matcher in order to tell if we're at
                # the end of the current file, not the end of the last block
                # of message headers.
                self._input.pop_eof_matcher()
                # The input stream must be sitting at the newline or at the
                # EOF.  We want to see if we're at the end of this subpart, so
                # first consume the blank line, then test the next line to see
                # if we're at this subpart's EOF.
                while True:
                    line = self._input.readline()
                    if line is NeedMoreData:
                        yield NeedMoreData
                        continue
                    break
                while True:
                    line = self._input.readline()
                    if line is NeedMoreData:
                        yield NeedMoreData
                        continue
                    break
                if line == '':
                    break
                # Not at EOF so this is a line we're going to need.
                self._input.unreadline(line)
            return
        if self._cur.get_content_maintype() == 'message':
            # The message claims to be a message/* type, then what follows is
            # another RFC 5322 message.
            for retval in self._parsegen():
                if retval is NeedMoreData:
                    yield NeedMoreData
                    continue
                break
            self._pop_message()
            return
        if self._cur.get_content_maintype() == 'multipart':
            boundary = self._cur.get_boundary()
            if boundary is None:
                # The message /claims/ to be a multipart but it has not
                # defined a boundary.  That's a problem which we'll handle by
                # reading everything until the EOF and marking the message as
                # defective.
                defect = errors.NoBoundaryInMultipartDefect()
                self.policy.handle_defect(self._cur, defect)
                lines = []
                for line in self._input:
                    if line is NeedMoreData:
                        yield NeedMoreData
                        continue
                    lines.append(line)
                self._cur.set_payload(EMPTYSTRING.join(lines))
                return
            # Make sure a valid content type was specified per RFC 2045:6.4.
            if (str(self._cur.get('content-transfer-encoding', '8bit')).lower()
                    not in ('7bit', '8bit', 'binary')):
                defect = errors.InvalidMultipartContentTransferEncodingDefect()
                self.policy.handle_defect(self._cur, defect)
            # Create a line match predicate which matches the inter-part
            # boundary as well as the end-of-multipart boundary.  Don't push
            # this onto the input stream until we've scanned past the
            # preamble.
            separator = '--' + boundary
            def boundarymatch(line):
                if not line.startswith(separator):
                    return None
                return boundaryendRE.match(line, len(separator))
            capturing_preamble = True
            preamble = []
            linesep = False
            close_boundary_seen = False
            while True:
                line = self._input.readline()
                if line is NeedMoreData:
                    yield NeedMoreData
                    continue
                if line == '':
                    break
                mo = boundarymatch(line)
                if mo:
                    # If we're looking at the end boundary, we're done with
                    # this multipart.  If there was a newline at the end of
                    # the closing boundary, then we need to initialize the
                    # epilogue with the empty string (see below).
                    if mo.group('end'):
                        close_boundary_seen = True
                        linesep = mo.group('linesep')
                        break
                    # We saw an inter-part boundary.  Were we in the preamble?
                    if capturing_preamble:
                        if preamble:
                            # According to RFC 2046, the last newline belongs
                            # to the boundary.
                            lastline = preamble[-1]
                            eolmo = NLCRE_eol.search(lastline)
                            if eolmo:
                                preamble[-1] = lastline[:-len(eolmo.group(0))]
                            self._cur.preamble = EMPTYSTRING.join(preamble)
                        capturing_preamble = False
                        self._input.unreadline(line)
                        continue
                    # We saw a boundary separating two parts.  Consume any
                    # multiple boundary lines that may be following.  Our
                    # interpretation of RFC 2046 BNF grammar does not produce
                    # body parts within such double boundaries.
                    while True:
                        line = self._input.readline()
                        if line is NeedMoreData:
                            yield NeedMoreData
                            continue
                        mo = boundarymatch(line)
                        if not mo:
                            self._input.unreadline(line)
                            break
                    # Recurse to parse this subpart; the input stream points
                    # at the subpart's first line.
                    self._input.push_eof_matcher(boundarymatch)
                    for retval in self._parsegen():
                        if retval is NeedMoreData:
                            yield NeedMoreData
                            continue
                        break
                    # Because of RFC 2046, the newline preceding the boundary
                    # separator actually belongs to the boundary, not the
                    # previous subpart's payload (or epilogue if the previous
                    # part is a multipart).
                    if self._last.get_content_maintype() == 'multipart':
                        epilogue = self._last.epilogue
                        if epilogue == '':
                            self._last.epilogue = None
                        elif epilogue is not None:
                            mo = NLCRE_eol.search(epilogue)
                            if mo:
                                end = len(mo.group(0))
                                self._last.epilogue = epilogue[:-end]
                    else:
                        payload = self._last._payload
                        if isinstance(payload, str):
                            mo = NLCRE_eol.search(payload)
                            if mo:
                                payload = payload[:-len(mo.group(0))]
                                self._last._payload = payload
                    self._input.pop_eof_matcher()
                    self._pop_message()
                    # Set the multipart up for newline cleansing, which will
                    # happen if we're in a nested multipart.
                    self._last = self._cur
                else:
                    # I think we must be in the preamble
                    assert capturing_preamble
                    preamble.append(line)
            # We've seen either the EOF or the end boundary.  If we're still
            # capturing the preamble, we never saw the start boundary.  Note
            # that as a defect and store the captured text as the payload.
            if capturing_preamble:
                defect = errors.StartBoundaryNotFoundDefect()
                self.policy.handle_defect(self._cur, defect)
                self._cur.set_payload(EMPTYSTRING.join(preamble))
                epilogue = []
                for line in self._input:
                    if line is NeedMoreData:
                        yield NeedMoreData
                        continue
                self._cur.epilogue = EMPTYSTRING.join(epilogue)
                return
            # If we're not processing the preamble, then we might have seen
            # EOF without seeing that end boundary...that is also a defect.
            if not close_boundary_seen:
                defect = errors.CloseBoundaryNotFoundDefect()
                self.policy.handle_defect(self._cur, defect)
                return
            # Everything from here to the EOF is epilogue.  If the end boundary
            # ended in a newline, we'll need to make sure the epilogue isn't
            # None
            if linesep:
                epilogue = ['']
            else:
                epilogue = []
            for line in self._input:
                if line is NeedMoreData:
                    yield NeedMoreData
                    continue
                epilogue.append(line)
            # Any CRLF at the front of the epilogue is not technically part of
            # the epilogue.  Also, watch out for an empty string epilogue,
            # which means a single newline.
            if epilogue:
                firstline = epilogue[0]
                bolmo = NLCRE_bol.match(firstline)
                if bolmo:
                    epilogue[0] = firstline[len(bolmo.group(0)):]
            self._cur.epilogue = EMPTYSTRING.join(epilogue)
            return
        # Otherwise, it's some non-multipart type, so the entire rest of the
        # file contents becomes the payload.
        lines = []
        for line in self._input:
            if line is NeedMoreData:
                yield NeedMoreData
                continue
            lines.append(line)
        self._cur.set_payload(EMPTYSTRING.join(lines))
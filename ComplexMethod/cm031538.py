def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.convert_charrefs and not self.cdata_elem:
                j = rawdata.find('<', i)
                if j < 0:
                    # if we can't find the next <, either we are at the end
                    # or there's more text incoming.  If the latter is True,
                    # we can't pass the text to handle_data in case we have
                    # a charref cut in half at end.  Try to determine if
                    # this is the case before proceeding by looking for an
                    # & near the end and see if it's followed by a space or ;.
                    amppos = rawdata.rfind('&', max(i, n-34))
                    if (amppos >= 0 and
                        not re.compile(r'[\t\n\r\f ;]').search(rawdata, amppos)):
                        break  # wait till we get all the text
                    j = n
            else:
                match = self.interesting.search(rawdata, i)  # < or &
                if match:
                    j = match.start()
                else:
                    if self.cdata_elem:
                        break
                    j = n
            if i < j:
                if self.convert_charrefs and self._escapable:
                    self.handle_data(unescape(rawdata[i:j]))
                else:
                    self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            if i == n: break
            startswith = rawdata.startswith
            if startswith('<', i):
                if starttagopen.match(rawdata, i): # < + letter
                    k = self.parse_starttag(i)
                elif startswith("</", i):
                    k = self.parse_endtag(i)
                elif startswith("<!--", i):
                    k = self.parse_comment(i)
                elif startswith("<?", i):
                    k = self.parse_pi(i)
                elif startswith("<!", i):
                    k = self.parse_html_declaration(i)
                elif (i + 1) < n or end:
                    self.handle_data("<")
                    k = i + 1
                else:
                    break
                if k < 0:
                    if not end:
                        break
                    if starttagopen.match(rawdata, i):  # < + letter
                        pass
                    elif startswith("</", i):
                        if i + 2 == n:
                            self.handle_data("</")
                        elif endtagopen.match(rawdata, i):  # </ + letter
                            pass
                        else:
                            # bogus comment
                            self.handle_comment(rawdata[i+2:])
                    elif startswith("<!--", i):
                        j = n
                        for suffix in ("--!", "--", "-"):
                            if rawdata.endswith(suffix, i+4):
                                j -= len(suffix)
                                break
                        self.handle_comment(rawdata[i+4:j])
                    elif startswith("<![CDATA[", i) and self._support_cdata:
                        self.unknown_decl(rawdata[i+3:])
                    elif rawdata[i:i+9].lower() == '<!doctype':
                        self.handle_decl(rawdata[i+2:])
                    elif startswith("<!", i):
                        # bogus comment
                        self.handle_comment(rawdata[i+2:])
                    elif startswith("<?", i):
                        self.handle_pi(rawdata[i+2:])
                    else:
                        raise AssertionError("we should not get here!")
                    k = n
                i = self.updatepos(i, k)
            elif startswith("&#", i):
                match = charref.match(rawdata, i)
                if match:
                    name = match.group()[2:-1]
                    self.handle_charref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                match = incomplete_charref.match(rawdata, i)
                if match:
                    if end:
                        self.handle_charref(rawdata[i+2:])
                        i = self.updatepos(i, n)
                        break
                    # incomplete
                    break
                elif i + 3 < n:  # larger than "&#x"
                    # not the end of the buffer, and can't be confused
                    # with some other construct
                    self.handle_data("&#")
                    i = self.updatepos(i, i + 2)
                else:
                    break
            elif startswith('&', i):
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                match = incomplete.match(rawdata, i)
                if match:
                    if end:
                        self.handle_entityref(rawdata[i+1:])
                        i = self.updatepos(i, n)
                        break
                    # incomplete
                    break
                elif i + 1 < n:
                    # not the end of the buffer, and can't be confused
                    # with some other construct
                    self.handle_data("&")
                    i = self.updatepos(i, i + 1)
                else:
                    break
            else:
                assert 0, "interesting.search() lied"
        # end while
        if end and i < n:
            if self.convert_charrefs and self._escapable:
                self.handle_data(unescape(rawdata[i:n]))
            else:
                self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)
        self.rawdata = rawdata[i:]
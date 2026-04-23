def parse_html_declaration(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i+2] == '<!', ('unexpected call to '
                                        'parse_html_declaration()')
        if rawdata[i:i+4] == '<!--':
            # this case is actually already handled in goahead()
            return self.parse_comment(i)
        elif rawdata[i:i+9] == '<![CDATA[' and self._support_cdata:
            j = rawdata.find(']]>', i+9)
            if j < 0:
                return -1
            self.unknown_decl(rawdata[i+3: j])
            return j + 3
        elif rawdata[i:i+9].lower() == '<!doctype':
            # find the closing >
            gtpos = rawdata.find('>', i+9)
            if gtpos == -1:
                return -1
            self.handle_decl(rawdata[i+2:gtpos])
            return gtpos+1
        else:
            return self.parse_bogus_comment(i)
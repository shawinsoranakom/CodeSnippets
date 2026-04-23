def parse_endtag(self, i):
        # See the HTML5 specs section "13.2.5.7 End tag open state"
        # https://html.spec.whatwg.org/multipage/parsing.html#end-tag-open-state
        rawdata = self.rawdata
        assert rawdata[i:i+2] == "</", "unexpected call to parse_endtag"
        if rawdata.find('>', i+2) < 0:  # fast check
            return -1
        if not endtagopen.match(rawdata, i):  # </ + letter
            if rawdata[i+2:i+3] == '>':  # </> is ignored
                # "missing-end-tag-name" parser error
                return i+3
            else:
                return self.parse_bogus_comment(i)

        match = locatetagend.match(rawdata, i+2)
        assert match
        j = match.end()
        if rawdata[j-1] != ">":
            return -1

        # find the name: "13.2.5.8 Tag name state"
        # https://html.spec.whatwg.org/multipage/parsing.html#tag-name-state
        match = tagfind_tolerant.match(rawdata, i+2)
        assert match
        tag = match.group(1).lower()
        self.handle_endtag(tag)
        self.clear_cdata_mode()
        return j
def parse_declaration(self, i):
        # This is some sort of declaration; in "HTML as
        # deployed," this should only be the document type
        # declaration ("<!DOCTYPE html...>").
        # ISO 8879:1986, however, has more complex
        # declaration syntax for elements in <!...>, including:
        # --comment--
        # [marked section]
        # name in the following list: ENTITY, DOCTYPE, ELEMENT,
        # ATTLIST, NOTATION, SHORTREF, USEMAP,
        # LINKTYPE, LINK, IDLINK, USELINK, SYSTEM
        rawdata = self.rawdata
        j = i + 2
        assert rawdata[i:j] == "<!", "unexpected call to parse_declaration"
        if rawdata[j:j+1] == ">":
            # the empty comment <!>
            return j + 1
        if rawdata[j:j+1] in ("-", ""):
            # Start of comment followed by buffer boundary,
            # or just a buffer boundary.
            return -1
        # A simple, practical version could look like: ((name|stringlit) S*) + '>'
        n = len(rawdata)
        if rawdata[j:j+2] == '--': #comment
            # Locate --.*-- as the body of the comment
            return self.parse_comment(i)
        elif rawdata[j] == '[': #marked section
            # Locate [statusWord [...arbitrary SGML...]] as the body of the marked section
            # Where statusWord is one of TEMP, CDATA, IGNORE, INCLUDE, RCDATA
            # Note that this is extended by Microsoft Office "Save as Web" function
            # to include [if...] and [endif].
            return self.parse_marked_section(i)
        else: #all other declaration elements
            decltype, j = self._scan_name(j, i)
        if j < 0:
            return j
        if decltype == "doctype":
            self._decl_otherchars = ''
        while j < n:
            c = rawdata[j]
            if c == ">":
                # end of declaration syntax
                data = rawdata[i+2:j]
                if decltype == "doctype":
                    self.handle_decl(data)
                else:
                    # According to the HTML5 specs sections "8.2.4.44 Bogus
                    # comment state" and "8.2.4.45 Markup declaration open
                    # state", a comment token should be emitted.
                    # Calling unknown_decl provides more flexibility though.
                    self.unknown_decl(data)
                return j + 1
            if c in "\"'":
                m = _declstringlit_match(rawdata, j)
                if not m:
                    return -1 # incomplete
                j = m.end()
            elif c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                name, j = self._scan_name(j, i)
            elif c in self._decl_otherchars:
                j = j + 1
            elif c == "[":
                # this could be handled in a separate doctype parser
                if decltype == "doctype":
                    j = self._parse_doctype_subset(j + 1, i)
                elif decltype in {"attlist", "linktype", "link", "element"}:
                    # must tolerate []'d groups in a content model in an element declaration
                    # also in data attribute specifications of attlist declaration
                    # also link type declaration subsets in linktype declarations
                    # also link attribute specification lists in link declarations
                    raise AssertionError("unsupported '[' char in %s declaration" % decltype)
                else:
                    raise AssertionError("unexpected '[' char in declaration")
            else:
                raise AssertionError("unexpected %r char in declaration" % rawdata[j])
            if j < 0:
                return j
        return -1
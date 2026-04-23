def __parse_string(self, str, patt=_CookiePattern):
        i = 0                 # Our starting point
        n = len(str)          # Length of string
        parsed_items = []     # Parsed (type, key, value) triples
        morsel_seen = False   # A key=value pair was previously encountered

        TYPE_ATTRIBUTE = 1
        TYPE_KEYVALUE = 2

        # We first parse the whole cookie string and reject it if it's
        # syntactically invalid (this helps avoid some classes of injection
        # attacks).
        while 0 <= i < n:
            # Start looking for a cookie
            match = patt.match(str, i)
            if not match:
                # No more cookies
                break

            key, value = match.group("key"), match.group("val")
            i = match.end(0)

            if key[0] == "$":
                if not morsel_seen:
                    # We ignore attributes which pertain to the cookie
                    # mechanism as a whole, such as "$Version".
                    # See RFC 2965. (Does anyone care?)
                    continue
                parsed_items.append((TYPE_ATTRIBUTE, key[1:], value))
            elif key.lower() in Morsel._reserved:
                if not morsel_seen:
                    # Invalid cookie string
                    return
                if value is None:
                    if key.lower() in Morsel._flags:
                        parsed_items.append((TYPE_ATTRIBUTE, key, True))
                    else:
                        # Invalid cookie string
                        return
                else:
                    parsed_items.append((TYPE_ATTRIBUTE, key, _unquote(value)))
            elif value is not None:
                parsed_items.append((TYPE_KEYVALUE, key, self.value_decode(value)))
                morsel_seen = True
            else:
                # Invalid cookie string
                return

        # The cookie string is valid, apply it.
        M = None         # current morsel
        for tp, key, value in parsed_items:
            if tp == TYPE_ATTRIBUTE:
                assert M is not None
                M[key] = value
            else:
                assert tp == TYPE_KEYVALUE
                rval, cval = value
                self.__set(key, rval, cval)
                M = self[key]
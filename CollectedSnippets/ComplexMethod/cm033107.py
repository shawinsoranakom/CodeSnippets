def _is_garbled_char(ch):
        """Check if a single character is garbled (unmappable from PDF font encoding).

        A character is considered garbled if it falls into Unicode Private Use Areas
        or certain replacement/control character ranges that typically indicate
        pdfminer failed to map a CID to a valid Unicode codepoint.
        """
        if not ch:
            return False
        cp = ord(ch)
        if 0xE000 <= cp <= 0xF8FF:
            return True
        if 0xF0000 <= cp <= 0xFFFFF:
            return True
        if 0x100000 <= cp <= 0x10FFFF:
            return True
        if cp == 0xFFFD:
            return True
        if cp < 0x20 and ch not in ('\t', '\n', '\r'):
            return True
        if 0x80 <= cp <= 0x9F:
            return True
        cat = unicodedata.category(ch)
        if cat in ("Cn", "Cs"):
            return True
        return False
def hex(self):
        "Return the hexadecimal representation of the WKB (a string)."
        return b2a_hex(self.wkb).upper()
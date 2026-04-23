def get_token(self):
        if self.pushback:
            return self.pushback.pop(0)
        token = ""
        fiter = iter(self._read_char, "")
        for ch in fiter:
            if ch in self.whitespace:
                continue
            if ch == '"':
                for ch in fiter:
                    if ch == '"':
                        return token
                    elif ch == "\\":
                        ch = self._read_char()
                    token += ch
            else:
                if ch == "\\":
                    ch = self._read_char()
                token += ch
                for ch in fiter:
                    if ch in self.whitespace:
                        return token
                    elif ch == "\\":
                        ch = self._read_char()
                    token += ch
        return token
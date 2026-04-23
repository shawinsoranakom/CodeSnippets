def search_forward(self, text, prog, line, col, wrap, ok=0):
        wrapped = 0
        startline = line
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        while chars:
            m = prog.search(chars[:-1], col)
            if m:
                if ok or m.end() > col:
                    return line, m
            line = line + 1
            if wrapped and line > startline:
                break
            col = 0
            ok = 1
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            if not chars and wrap:
                wrapped = 1
                wrap = 0
                line = 1
                chars = text.get("1.0", "2.0")
        return None
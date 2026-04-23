def search_backward(self, text, prog, line, col, wrap, ok=0):
        wrapped = 0
        startline = line
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        while True:
            m = search_reverse(prog, chars[:-1], col)
            if m:
                if ok or m.start() < col:
                    return line, m
            line = line - 1
            if wrapped and line < startline:
                break
            ok = 1
            if line <= 0:
                if not wrap:
                    break
                wrapped = 1
                wrap = 0
                pos = text.index("end-1c")
                line, col = map(int, pos.split("."))
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            col = len(chars) - 1
        return None
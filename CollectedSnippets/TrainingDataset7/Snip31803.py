def makefile(mode, *a, **kw):
            if mode == "rb":
                return rfile
            elif mode == "wb":
                return wfile
def load_module(self, fqname, fp, pathname, file_info):
        suffix, mode, type = file_info
        self.msgin(2, "load_module", fqname, fp and "fp", pathname)
        if type == _PKG_DIRECTORY:
            m = self.load_package(fqname, pathname)
            self.msgout(2, "load_module ->", m)
            return m
        if type == _PY_SOURCE:
            co = compile(fp.read(), pathname, 'exec', module=fqname)
        elif type == _PY_COMPILED:
            try:
                data = fp.read()
                importlib._bootstrap_external._classify_pyc(data, fqname, {})
            except ImportError as exc:
                self.msgout(2, "raise ImportError: " + str(exc), pathname)
                raise
            co = marshal.loads(memoryview(data)[16:])
        else:
            co = None
        m = self.add_module(fqname)
        m.__file__ = pathname
        if co:
            if self.replace_paths:
                co = self.replace_paths_in_code(co)
            m.__code__ = co
            self.scan_code(co, m)
        self.msgout(2, "load_module ->", m)
        return m
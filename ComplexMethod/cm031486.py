def load_extension(self, name):
        fname = self.extfiles.get(name, name)
        try:
            try:
                mod = importlib.import_module('.' + fname, package=__package__)
            except (ImportError, TypeError):
                mod = importlib.import_module(fname)
        except ImportError:
            print("\nFailed to import extension: ", name)
            raise
        cls = getattr(mod, name)
        keydefs = idleConf.GetExtensionBindings(name)
        if hasattr(cls, "menudefs"):
            self.fill_menus(cls.menudefs, keydefs)
        ins = cls(self)
        self.extensions[name] = ins
        if keydefs:
            self.apply_bindings(keydefs)
            for vevent in keydefs:
                methodname = vevent.replace("-", "_")
                while methodname[:1] == '<':
                    methodname = methodname[1:]
                while methodname[-1:] == '>':
                    methodname = methodname[:-1]
                methodname = methodname + "_event"
                if hasattr(ins, methodname):
                    self.text.bind(vevent, getattr(ins, methodname))
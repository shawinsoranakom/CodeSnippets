def find_class(self, module, name):
        # Subclasses may override this.
        sys.audit('pickle.find_class', module, name)
        if self.proto < 3 and self.fix_imports:
            if (module, name) in _compat_pickle.NAME_MAPPING:
                module, name = _compat_pickle.NAME_MAPPING[(module, name)]
            elif module in _compat_pickle.IMPORT_MAPPING:
                module = _compat_pickle.IMPORT_MAPPING[module]
        __import__(module, level=0)
        if self.proto >= 4 and '.' in name:
            dotted_path = name.split('.')
            try:
                return _getattribute(sys.modules[module], dotted_path)
            except AttributeError:
                raise AttributeError(
                    f"Can't resolve path {name!r} on module {module!r}")
        else:
            return getattr(sys.modules[module], name)
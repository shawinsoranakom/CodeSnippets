def _do_find_and_load(self, name):
        parent = name.rpartition(".")[0]
        module_name_no_parent = name.rpartition(".")[-1]
        if parent:
            if parent not in self.modules:
                self._gcd_import(parent)
            # Crazy side-effects!
            if name in self.modules:
                return self.modules[name]
            parent_module = self.modules[parent]

            try:
                parent_module.__path__  # type: ignore[attr-defined]

            except AttributeError:
                # when we attempt to import a package only containing pybinded files,
                # the parent directory isn't always a package as defined by python,
                # so we search if the package is actually there or not before calling the error.
                if isinstance(
                    parent_module.__loader__,
                    importlib.machinery.ExtensionFileLoader,
                ):
                    if name not in self.extern_modules:
                        msg = (
                            _ERR_MSG
                            + "; {!r} is a c extension module which was not externed. C extension modules \
                            need to be externed by the PackageExporter in order to be used as we do not support interning them.}."
                        ).format(name, name)
                        raise ModuleNotFoundError(msg, name=name) from None
                    if not isinstance(
                        parent_module.__dict__.get(module_name_no_parent),
                        types.ModuleType,
                    ):
                        msg = (
                            _ERR_MSG
                            + "; {!r} is a c extension package which does not contain {!r}."
                        ).format(name, parent, name)
                        raise ModuleNotFoundError(msg, name=name) from None
                else:
                    msg = (_ERR_MSG + "; {!r} is not a package").format(name, parent)
                    raise ModuleNotFoundError(msg, name=name) from None

        module = self._load_module(name, parent)

        self._install_on_parent(parent, name, module)

        return module
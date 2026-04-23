def _load_module(self, name: str, parent: str):
        cur: _PathNode = self.root
        for atom in name.split("."):
            if not isinstance(cur, _PackageNode) or atom not in cur.children:
                if name in IMPLICIT_IMPORT_ALLOWLIST:
                    module = self.modules[name] = importlib.import_module(name)
                    return module
                raise ModuleNotFoundError(
                    f'No module named "{name}" in self-contained archive "{self.filename}"'
                    f" and the module is also not in the list of allowed external modules: {self.extern_modules}",
                    name=name,
                )
            cur = cur.children[atom]
            if isinstance(cur, _ExternNode):
                module = self.modules[name] = importlib.import_module(name)

                if compat_mapping := EXTERN_IMPORT_COMPAT_NAME_MAPPING.get(name):
                    for old_name, new_name in compat_mapping.items():
                        module.__dict__.setdefault(old_name, new_name)

                return module
        return self._make_module(
            name,
            cur.source_file,  # type: ignore[attr-defined]
            isinstance(cur, _PackageNode),
            parent,
        )
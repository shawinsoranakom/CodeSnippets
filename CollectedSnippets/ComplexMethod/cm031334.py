def _maybe_import_module(self, fqname: str) -> ModuleType | None:
        if any(pattern.fullmatch(fqname) for pattern in AUTO_IMPORT_DENYLIST):
            # Special-cased modules with known import side-effects
            return None
        root = fqname.split(".")[0]
        mod_info = next((m for m in self.global_cache if m.name == root), None)
        if not mod_info or not self._is_stdlib_module(mod_info):
            # Only import stdlib modules (no risk of import side-effects)
            return None
        try:
            return importlib.import_module(fqname)
        except Exception:
            sys.modules.pop(fqname, None)  # Clean half-imported module
            return None
def _find_modules(self, path: str, prefix: str) -> list[str]:
        if not path:
            # Top-level import (e.g. `import foo<tab>`` or `from foo<tab>`)`
            builtin_modules = [name for name in sys.builtin_module_names
                               if self.is_suggestion_match(name, prefix)]
            third_party_modules = [module.name for module in self.global_cache
                                   if self.is_suggestion_match(module.name, prefix)]
            return sorted(builtin_modules + third_party_modules)

        path = self._resolve_relative_path(path)  # type: ignore[assignment]
        if path is None:
            return []

        modules: Iterable[pkgutil.ModuleInfo] = self.global_cache
        imported_module = sys.modules.get(path.split('.')[0])
        if imported_module:
            # Filter modules to those whose name and specs match the
            # imported module to avoid invalid suggestions
            spec = imported_module.__spec__
            if spec:
                def _safe_find_spec(mod: pkgutil.ModuleInfo) -> bool:
                    try:
                        return mod.module_finder.find_spec(mod.name, None) == spec
                    except Exception:
                        return False
                modules = [mod for mod in modules
                           if mod.name == spec.name
                           and _safe_find_spec(mod)]
            else:
                modules = []

        is_stdlib_import: bool | None = None
        for segment in path.split('.'):
            modules = [mod_info for mod_info in modules
                       if mod_info.ispkg and mod_info.name == segment]
            if is_stdlib_import is None:
                # Top-level import decide if we import from stdlib or not
                is_stdlib_import = all(
                    self._is_stdlib_module(mod_info) for mod_info in modules
                )
            modules = self.iter_submodules(modules)

        module_names = [module.name for module in modules]
        if is_stdlib_import:
            module_names.extend(HARDCODED_SUBMODULES.get(path, ()))
        return [module_name for module_name in module_names
                if self.is_suggestion_match(module_name, prefix)]
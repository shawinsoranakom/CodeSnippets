def _find_attributes(self, path: str, prefix: str) -> tuple[list[str], CompletionAction | None]:
        path = self._resolve_relative_path(path)  # type: ignore[assignment]
        if path is None:
            return [], None

        imported_module = sys.modules.get(path)
        if not imported_module:
            if path in self._failed_imports:  # Do not propose to import again
                return [], None
            imported_module = self._maybe_import_module(path)
        if not imported_module:
            return [], self._get_import_completion_action(path)
        try:
            module_attributes = dir(imported_module)
        except Exception:
            module_attributes = []
        return [attr_name for attr_name in module_attributes
                if self.is_suggestion_match(attr_name, prefix)], None
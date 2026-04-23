def _register_necessary_watchers(self, module_paths: Dict[str, Set[str]]) -> None:
        for name, paths in module_paths.items():
            for path in paths:
                if self._file_should_be_watched(path):
                    self._register_watcher(path, name)
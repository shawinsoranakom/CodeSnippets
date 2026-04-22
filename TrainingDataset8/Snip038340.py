def _exclude_blacklisted_paths(self, paths: Set[str]) -> Set[str]:
        return {p for p in paths if not self._folder_black_list.is_blacklisted(p)}
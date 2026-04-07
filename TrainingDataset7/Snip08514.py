def _resolve_child(self, path_segment, create_if_missing, child_cls):
        if create_if_missing:
            self._update_accessed_time()
            self._update_modified_time()
            if child_cls is InMemoryFileNode:
                child = child_cls(name=path_segment)
            else:
                child = child_cls()
            return self._children.setdefault(path_segment, child)
        return self._children.get(path_segment)
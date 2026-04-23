def __dir__(self):
        """Filter the output of `dir(mock)` to only useful members."""
        if not FILTER_DIR:
            return object.__dir__(self)

        extras = self._mock_methods or []
        from_type = dir(type(self))
        from_dict = list(self.__dict__)
        from_child_mocks = [
            m_name for m_name, m_value in self._mock_children.items()
            if m_value is not _deleted]

        from_type = [e for e in from_type if not e.startswith('_')]
        from_dict = [e for e in from_dict if not e.startswith('_') or
                     _is_magic(e)]
        return sorted(set(extras + from_type + from_dict + from_child_mocks))
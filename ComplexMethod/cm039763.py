def properties(self):
        if self._cls is None:
            return []
        return [
            name
            for name, func in inspect.getmembers(self._cls)
            if (
                not name.startswith("_")
                and not self._should_skip_member(name, self._cls)
                and (
                    func is None
                    or isinstance(func, (property, cached_property))
                    or inspect.isdatadescriptor(func)
                )
                and self._is_show_member(name)
            )
        ]
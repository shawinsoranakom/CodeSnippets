def __getstate__(self):
        """Hook to allow choosing the attributes to pickle."""
        state = self.__dict__.copy()
        state["_state"] = copy.copy(state["_state"])
        state["_state"].fields_cache = state["_state"].fields_cache.copy()
        # memoryview cannot be pickled, so cast it to bytes and store
        # separately.
        _memoryview_attrs = []
        for attr, value in state.items():
            if isinstance(value, memoryview):
                _memoryview_attrs.append((attr, bytes(value)))
        if _memoryview_attrs:
            state["_memoryview_attrs"] = _memoryview_attrs
            for attr, value in _memoryview_attrs:
                state.pop(attr)
        return state
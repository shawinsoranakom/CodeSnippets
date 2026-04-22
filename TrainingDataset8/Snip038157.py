def _getitem(self, widget_id: Optional[str], user_key: Optional[str]) -> Any:
        """Get the value of an entry in Session State, using either the
        user-provided key or a widget id as appropriate for the internal dict
        being accessed.

        At least one of the arguments must have a value."""
        assert user_key is not None or widget_id is not None

        if user_key is not None:
            try:
                return self._new_session_state[user_key]
            except KeyError:
                pass

        if widget_id is not None:
            try:
                return self._new_widget_state[widget_id]
            except KeyError:
                pass

        # Typically, there won't be both a widget id and an associated state key in
        # old state at the same time, so the order we check is arbitrary.
        # The exception is if session state is set and then a later run has
        # a widget created, so the widget id entry should be newer.
        # The opposite case shouldn't happen, because setting the value of a widget
        # through session state will result in the next widget state reflecting that
        # value.
        if widget_id is not None:
            try:
                return self._old_state[widget_id]
            except KeyError:
                pass

        if user_key is not None:
            try:
                return self._old_state[user_key]
            except KeyError:
                pass

        # We'll never get here
        raise KeyError
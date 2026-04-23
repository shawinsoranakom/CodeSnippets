def to_dict(self) -> Dict[str, Any]:
        """Return a dict containing all session_state and keyed widget values."""
        return get_session_state().filtered_state
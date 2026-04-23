def __str__(self) -> str:
        """String representation of user state and keyed widget values."""
        return str(get_session_state().filtered_state)
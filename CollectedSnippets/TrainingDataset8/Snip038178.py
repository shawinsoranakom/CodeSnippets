def __len__(self) -> int:
        """Number of user state and keyed widget values in session_state."""
        return len(get_session_state().filtered_state)
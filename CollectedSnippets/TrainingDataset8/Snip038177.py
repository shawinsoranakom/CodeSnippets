def __iter__(self) -> Iterator[Any]:
        """Iterator over user state and keyed widget values."""
        # TODO: this is unsafe if fastReruns is true! Let's deprecate/remove.
        return iter(get_session_state().filtered_state)
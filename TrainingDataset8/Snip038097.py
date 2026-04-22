def _maybe_delete_environment_variable(k: Any, v: Any) -> None:
        """Remove the given key/value pair from os.environ if the value
        is a string, int, or float."""
        value_type = type(v)
        if value_type in (str, int, float) and os.environ.get(k) == v:
            del os.environ[k]
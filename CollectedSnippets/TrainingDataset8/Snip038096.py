def _maybe_set_environment_variable(k: Any, v: Any) -> None:
        """Add the given key/value pair to os.environ if the value
        is a string, int, or float."""
        value_type = type(v)
        if value_type in (str, int, float):
            os.environ[k] = str(v)
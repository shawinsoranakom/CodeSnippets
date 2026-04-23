def get_from_env_fn() -> str | None:
        """Get a value from an environment variable.

        Raises:
            ValueError: If the environment variable is not set and no default is
                provided.

        Returns:
            The value from the environment.
        """
        if isinstance(key, (list, tuple)):
            for k in key:
                if k in os.environ:
                    return os.environ[k]
        if isinstance(key, str) and key in os.environ:
            return os.environ[key]

        if isinstance(default, (str, type(None))):
            return default
        if error_message:
            raise ValueError(error_message)
        msg = (
            f"Did not find {key}, please add an environment variable"
            f" `{key}` which contains it, or pass"
            f" `{key}` as a named parameter."
        )
        raise ValueError(msg)
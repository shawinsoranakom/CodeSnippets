def _validate_databases(cls):
        if cls.databases == "__all__":
            return frozenset(connections)
        for alias in cls.databases:
            if alias not in connections:
                message = (
                    "%s.%s.databases refers to %r which is not defined in "
                    "settings.DATABASES."
                    % (
                        cls.__module__,
                        cls.__qualname__,
                        alias,
                    )
                )
                close_matches = get_close_matches(alias, list(connections))
                if close_matches:
                    message += " Did you mean %r?" % close_matches[0]
                raise ImproperlyConfigured(message)
        return frozenset(cls.databases)
def _add_databases_failures(cls):
        cls.databases = cls._validate_databases()
        for alias in connections:
            if alias in cls.databases:
                continue
            connection = connections[alias]
            for name, operation in cls._disallowed_connection_methods:
                message = cls._disallowed_database_msg % {
                    "test": "%s.%s" % (cls.__module__, cls.__qualname__),
                    "alias": alias,
                    "operation": operation,
                }
                method = getattr(connection, name)
                setattr(connection, name, _DatabaseFailure(method, message))
        cls.enterClassContext(
            mock.patch.object(
                BaseDatabaseWrapper,
                "ensure_connection",
                new=cls.ensure_connection_patch_method(),
            )
        )
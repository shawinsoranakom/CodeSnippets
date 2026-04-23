def patched_ensure_connection(self, *args, **kwargs):
            if (
                self.connection is None
                and self.alias not in cls.databases
                and self.alias != NO_DB_ALIAS
                # Dynamically created connections are always allowed.
                and self.alias in connections
            ):
                # Connection has not yet been established, but the alias is not
                # allowed.
                message = cls._disallowed_database_msg % {
                    "test": f"{cls.__module__}.{cls.__qualname__}",
                    "alias": self.alias,
                    "operation": "threaded connections",
                }
                return _DatabaseFailure(self.ensure_connection, message)()

            real_ensure_connection(self, *args, **kwargs)
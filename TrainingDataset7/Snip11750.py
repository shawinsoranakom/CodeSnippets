def as_mysql(self, compiler, connection, **extra_context):
        if connection.features.supports_uuid7_function:
            return self.as_sql(
                compiler, connection, function="UUID_V7", **extra_context
            )
        if connection.mysql_is_mariadb:
            raise NotSupportedError("UUID7 requires MariaDB version 11.7 or later.")
        raise NotSupportedError("UUID7 is not supported on MySQL.")
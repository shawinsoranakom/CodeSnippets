def as_mysql(self, compiler, connection, **extra_context):
        if not connection.features.supports_uuid4_function:
            if connection.mysql_is_mariadb:
                raise NotSupportedError("UUID4 requires MariaDB version 11.7 or later.")
            raise NotSupportedError("UUID4 is not supported on MySQL.")
        return self.as_sql(compiler, connection, function="UUID_V4", **extra_context)
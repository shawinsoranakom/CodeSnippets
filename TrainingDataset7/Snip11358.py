def as_mysql(self, compiler, connection):
        # The ->> operator is not supported on MariaDB (see MDEV-13594) and
        # only supported against columns on MySQL.
        if (
            connection.mysql_is_mariadb
            or getattr(self.lhs.output_field, "model", None) is None
        ):
            sql, params = super().as_mysql(compiler, connection)
            return "JSON_UNQUOTE(%s)" % sql, params
        else:
            lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
            json_path = connection.ops.compile_json_path(key_transforms)
            return "(%s ->> %%s)" % lhs, (*params, json_path)
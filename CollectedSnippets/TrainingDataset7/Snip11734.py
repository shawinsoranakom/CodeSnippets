def as_oracle(self, compiler, connection, **extra_context):
        # REVERSE in Oracle is undocumented and doesn't support multi-byte
        # strings. Use a special subquery instead.
        suffix = connection.features.bare_select_suffix
        sql, params = super().as_sql(
            compiler,
            connection,
            template=(
                "(SELECT LISTAGG(s) WITHIN GROUP (ORDER BY n DESC) FROM "
                f"(SELECT LEVEL n, SUBSTR(%(expressions)s, LEVEL, 1) s{suffix} "
                "CONNECT BY LEVEL <= LENGTH(%(expressions)s)) "
                "GROUP BY %(expressions)s)"
            ),
            **extra_context,
        )
        return sql, params * 3